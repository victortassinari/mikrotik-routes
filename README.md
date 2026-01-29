# MikroTik Link Dashboard

App pra chavear link no MikroTik sem precisar abrir Winbox ou acessar via web. O script descobre os links sozinho pelas rotas e deixa você trocar de provedor ou ativar o failover automático com um clique.

---

## Como funciona

### No MikroTik
O segredo tá nos **comentários** das rotas default (`0.0.0.0/0`).
O app procura por qualquer rota que o comentário comece com `Link`.
- Exemplo: Se você comentar uma rota como `Link_Vivo` e outra como `Link_Starlink`, elas vão aparecer como botões no app.

### No App
1. Faz o login com IP, user e senha (ele salva o host/user pra prox vez).
2. A senha fica guardada no Windows Vault (Keyring), não fica em texto plano.
3. Se fechar a janela, ele fica minimizado no tray (bandeja do sistema).
4. Botão **Ativar Failover**: Habilita todas as rotas de link de uma vez.
5. Botão de cada link: Habilita só aquele e desabilita os outros (modo manual).
6. **Monitoramento de Latência**: Mostra o ping real (em ms) de cada link abaixo dos botões.
   - Atualiza a cada 5 segundos automaticamente.
   - Funciona mesmo com links desabilitados (não ativos).

### Como o Ping Funciona
O app testa a latência de **todos os links** (ativos ou não) pingando `8.8.8.8`:

- **Links PPPoE/VPN** (ex: `LINK1_CityNet_PPPoE`):
  - Usa o parâmetro `interface=` do MikroTik para forçar o ping pela interface virtual.
  
- **Links DHCP/Estáticos** (ex: `LINK3_Starlink` com gateway `192.168.1.1`):
  - Busca automaticamente o IP obtido via DHCP client.
  - Usa `src-address=` para forçar o pacote a sair pela interface física correta.
  - Equivalente ao comando: `/ping 8.8.8.8 src-address=192.168.1.191`

- **Indicação Visual**:
  - 🟢 Verde: Latência boa (< 100ms)
  - 🟡 Laranja: Latência alta (100-200ms)
  - 🔴 Vermelho: Latência crítica (> 200ms) ou link offline (`-`)

---

## Dev / Build

Se quiser rodar direto (Windows):
```bash
# Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py
```

Pra gerar o `.exe` pro Windows:
```bash
./scripts/build_exe.bat
```
*(O script já cuida de fechar o exe se tiver aberto e limpa os arquivos temporários).*

---

## English (Quick Docs)

Simple dashboard to switch MikroTik links. It auto-discovers routes based on their comments.

- **Setup:** Add comments starting with `Link` to your `0.0.0.0/0` routes (e.g., `Link_ISP1`).
- **Security:** Passwords are stored securely in Windows Keyring.
- **Tray:** Runs in background (system tray) when closed.
- **Build:** Just run `scripts/build_exe.bat` to create a standalone executable.
Raw documentation at `scripts/build_exe.bat`.

---

## Pendências / TODO

- [x] Criar ícone (.ico) próprio para o executável.
- [ ] Testar e gerar versão funcional para **Linux** (ajustar caminhos e dependências de tray).
- [x] Adicionar suporte a HTTPS na API do RouterOS.
- [x] Implementar log de erros em arquivo local para facilitar debug.
