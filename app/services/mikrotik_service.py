import routeros_api
import re
from app.services.logger_service import logger


class MikrotikService:
    def __init__(self, host, user, password, use_ssl=False):
        self.host = host
        self.user = user
        self.password = password
        self.use_ssl = use_ssl

    def _get_connection(self):
        return routeros_api.RouterOsApiPool(
            self.host, 
            username=self.user, 
            password=self.password, 
            plaintext_login=True,
            use_ssl=self.use_ssl
        )

    def discover_links(self):
        """Busca os links disponíveis no MikroTik."""
        connection = self._get_connection()
        try:
            api = connection.get_api()
            list_routes = api.get_resource('/ip/route')
            
            routes = list_routes.get(dst_address='0.0.0.0/0')
            discovered = []
            
            for r in routes:
                comment = r.get('comment', '')
                if comment.startswith("Link"):
                    label = comment.split('_')[-1] if '_' in comment else comment
                    gateway = r.get('gateway', '')
                    discovered.append({'comment': comment, 'label': label, 'gateway': gateway})
            
            discovered.sort(key=lambda x: x['comment'])
            logger.info(f"Discovered {len(discovered)} links: {[d['label'] for d in discovered]}")
            return discovered
        except Exception as e:
            logger.error(f"Error discovering links on {self.host}: {e}")
            raise
        finally:
            connection.disconnect()

    def get_status(self, discovered_links):
        """Busca Link Ativo, Modo e Pings no MikroTik."""
        active_link = "Desconhecido"
        mode = "Manual"
        unreachable_links = []
        pings = {}  # {comment: ms}
        
        # Initialize all pings as "checking" to show user that verification is in progress
        for link in discovered_links:
            pings[link['comment']] = "checking"
        
        connection = self._get_connection()
        try:
            api = connection.get_api()
            list_routes = api.get_resource('/ip/route')
            all_default_routes = list_routes.get(dst_address='0.0.0.0/0')
            
            enabled_count = 0
            
            # Fetch DHCP clients and IP addresses to find source IPs for forced pings
            dhcp_clients = []
            ip_addresses = []
            try:
                dhcp_clients = api.get_resource('/ip/dhcp-client').get()
                ip_addresses = api.get_resource('/ip/address').get()
                logger.info(f"Found {len(dhcp_clients)} DHCP clients: {[d.get('interface') + '=' + d.get('gateway', 'N/A') for d in dhcp_clients]}")
            except Exception as e:
                logger.warning(f"Could not fetch DHCP/IP info for better pinging: {e}")
            
            # Prep ping targets and interfaces
            ping_configs = {} # comment -> {params}
            
            for route in all_default_routes:
                comment = route.get('comment', '')
                matched_link = next((l for l in discovered_links if l['comment'] in comment), None)
                
                if matched_link:
                    is_disabled = route.get('disabled') == 'true'
                    is_active = route.get('active') == 'true'
                    
                    if not is_disabled:
                        enabled_count += 1
                        gw_status = route.get('gateway-status', '').lower()
                        if 'unreachable' in gw_status or (not is_active and enabled_count == 1 and not is_disabled):
                            unreachable_links.append(matched_link['comment'])
                    
                    if is_active:
                        active_link = matched_link['label']

                    # ============================================================
                    # PING CONFIGURATION LOGIC
                    # ============================================================
                    # Goal: Ping 8.8.8.8 through each WAN link to measure real latency,
                    # even when the link is not the active default route.
                    #
                    # Strategy by link type:
                    # 1. PPPoE/VPN links (e.g., LINK1_CityNet_PPPoE):
                    #    - Use: interface=<interface_name>
                    #    - MikroTik can route through the interface directly
                    #
                    # 2. DHCP/Static links with physical interface (e.g., LINK3_Starlink):
                    #    - Use: src-address=<dhcp_client_ip>
                    #    - Forces the packet to exit via the correct WAN by source IP
                    #    - DHCP client is found by matching gateway IP (e.g., 192.168.1.1)
                    #
                    # 3. Fallback (no interface or source IP found):
                    #    - Ping the gateway IP directly (limited usefulness)
                    # ============================================================
                    
                    # Ping Configuration Logic: Try to find physical interface 
                    # to force ping through the correct path even if not active.
                    gw_raw = route.get('gateway', '')
                    gw_status = route.get('gateway-status', '')
                    p_params = {'count': '1', 'address': '8.8.8.8'}
                    
                    logger.info(f"Route Debug: {comment} -> gw='{gw_raw}', gw_status='{gw_status}'")
                    
                    iface = None
                    if '%' in gw_raw:
                        iface = gw_raw.split('%')[-1]
                    elif any(c.isalpha() for c in gw_raw):
                        iface = gw_raw
                    elif 'via' in gw_status:
                        # Extract interface name after "via" (e.g. "reachable via ether1")
                        try:
                            iface = gw_status.split('via')[-1].strip().split()[0]
                        except: pass
                    
                    # Better forcing: Find Source IP for this interface
                    # This is key for DHCP/Static links to route 8.8.8.8 correctly
                    src_ip = None
                    is_pppoe = iface and ('pppoe' in iface.lower() or 'vpn' in iface.lower())
                    
                    logger.info(f"Ping Config Debug: {comment} -> iface='{iface}', is_pppoe={is_pppoe}, gw_raw='{gw_raw}'")
                    
                    if iface and not is_pppoe:
                        # For non-PPPoE interfaces (DHCP/Static), we need src-address
                        # Check DHCP bound address
                        dhcp = next((d for d in dhcp_clients if d.get('interface') == iface and d.get('status') == 'bound'), None)
                        logger.info(f"  DHCP lookup for {iface}: {dhcp}")
                        if dhcp:
                            src_ip = dhcp.get('address', '').split('/')[0]
                        else:
                            # Check static IP Address list
                            addr = next((a for a in ip_addresses if a.get('interface') == iface), None)
                            logger.info(f"  IP Address lookup for {iface}: {addr}")
                            if addr:
                                src_ip = addr.get('address', '').split('/')[0]
                        logger.info(f"  Found src_ip: {src_ip}")
                    elif not iface and gw_raw and not any(c.isalpha() for c in gw_raw):
                        # Gateway is an IP but no interface found - search DHCP by gateway
                        logger.info(f"  Searching DHCP client by gateway IP: {gw_raw}")
                        dhcp = next((d for d in dhcp_clients if d.get('gateway') == gw_raw and d.get('status') == 'bound'), None)
                        logger.info(f"  DHCP lookup by gateway: {dhcp}")
                        if dhcp:
                            src_ip = dhcp.get('address', '').split('/')[0]
                            logger.info(f"  Found src_ip from DHCP gateway: {src_ip}")
                        else:
                            # DHCP client not found - likely cable disconnected or interface down
                            logger.warning(f"  No DHCP client found for gateway {gw_raw} - marking as offline")
                            pings[matched_link['comment']] = "err"
                            ping_configs[matched_link['comment']] = None  # Skip ping attempt
                            continue
                    
                    if src_ip:
                        # Use src-address for DHCP/Static links (not PPPoE)
                        p_params['src-address'] = src_ip
                        # Don't use interface parameter with src-address
                        # p_params already has address=8.8.8.8
                    elif iface:
                        # For PPPoE, use interface parameter only
                        p_params['interface'] = iface
                    else:
                        # Fallback to pinging the gateway IP if no way to force 8.8.8.8
                        p_params['address'] = gw_raw.split('%')[0]
                    
                    ping_configs[matched_link['comment']] = p_params

            # Quick pings for each link (timeout 1s each)
            ping_resource = api.get_resource('/tool')
            for comment, params in ping_configs.items():
                if params is None:
                    # Link was marked as offline during config phase
                    continue
                try:
                    logger.info(f"Ping Executing: {comment} -> {params}")
                    res = ping_resource.call('ping', params)
                    if res and len(res) > 0:
                        avg_rtt = str(res[0].get('avg-rtt', ''))
                        logger.info(f"Ping Result: {comment} ({params.get('interface', params.get('address'))}) -> '{avg_rtt}'")
                        if avg_rtt:
                            # Handle composite format: "10ms247us"
                            ms = 0
                            us = 0
                            ms_match = re.search(r'(\d+)\s*ms', avg_rtt)
                            if ms_match:
                                ms = int(ms_match.group(1))
                            us_match = re.search(r'(\d+)\s*us', avg_rtt)
                            if us_match:
                                us = int(us_match.group(1))
                            
                            if ms_match or us_match:
                                total_ms = ms + (us / 1000.0)
                                pings[comment] = str(round(total_ms, 1))
                            elif ':' in avg_rtt and '.' in avg_rtt:
                                # Format HH:MM:SS.mmm -> extract milliseconds
                                try:
                                    ms_part = avg_rtt.split('.')[-1]
                                    total_ms = float("0." + ms_part) * 1000
                                    pings[comment] = str(round(total_ms, 1))
                                except:
                                    pings[comment] = "0"
                            else:
                                # Strip any non-numeric chars but keep it simple
                                clean_val = "".join(filter(lambda x: x.isdigit() or x == '.', avg_rtt))
                                pings[comment] = clean_val if clean_val else "timeout"
                        else:
                            pings[comment] = "timeout"
                    else:
                        pings[comment] = "timeout"
                except Exception:
                    pings[comment] = "err"

            if enabled_count > 1:
                mode = "Failover Automático"
            else:
                mode = "Manual"
                
            return active_link, mode, unreachable_links, pings
        except Exception as e:
            logger.error(f"Error getting status from {self.host}: {e}")
            raise
        finally:
            connection.disconnect()

    def switch_link(self, target_comment, discovered_links):
        """Ativa um link específico e desabilita os outros."""
        connection = self._get_connection()
        try:
            api = connection.get_api()
            list_routes = api.get_resource('/ip/route')
            routes = list_routes.get(dst_address='0.0.0.0/0')

            for route in routes:
                comment = route.get('comment', '')
                if any(link['comment'] in comment for link in discovered_links):
                    if target_comment in comment:
                        list_routes.set(id=route['id'], disabled='no')
                    else:
                        list_routes.set(id=route['id'], disabled='yes')
            logger.info(f"Switched link to {target_comment}")
        except Exception as e:
            logger.error(f"Error switching link to {target_comment} on {self.host}: {e}")
            raise
        finally:
            connection.disconnect()

    def enable_all_links(self, discovered_links):
        """Habilita todos os links para failover automático."""
        connection = self._get_connection()
        try:
            api = connection.get_api()
            list_routes = api.get_resource('/ip/route')
            routes = list_routes.get(dst_address='0.0.0.0/0')

            for route in routes:
                comment = route.get('comment', '')
                if any(link['comment'] in comment for link in discovered_links):
                    list_routes.set(id=route['id'], disabled='no')
        finally:
            connection.disconnect()
