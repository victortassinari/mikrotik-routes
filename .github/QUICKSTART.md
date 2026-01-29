# 🚀 Guia Rápido - Git & GitHub Actions

## 📦 Fazer Commit e Gerar Release Automática

```bash
# 1. Adicionar arquivos modificados
git add .

# 2. Fazer commit com mensagem descritiva
git commit -m "feat: adiciona monitoramento de latência em tempo real"

# 3. Enviar para o GitHub (dispara o build automático)
git push origin main
```

✅ **Resultado:** Uma nova release será criada automaticamente em ~5 minutos!

---

## 🏷️ Criar Release Versionada (Opcional)

Se você preferir controlar as versões manualmente:

```bash
# 1. Criar tag com versionamento semântico
git tag -a v1.0.0 -m "Release 1.0.0 - Versão inicial estável"

# 2. Enviar a tag para o GitHub
git push origin v1.0.0
```

### Padrão de Versionamento (Semantic Versioning)

- **v1.0.0** → Major.Minor.Patch
  - **Major (1.x.x)**: Mudanças incompatíveis com versões anteriores
  - **Minor (x.1.x)**: Novas funcionalidades compatíveis
  - **Patch (x.x.1)**: Correções de bugs

**Exemplos:**
```bash
git tag -a v1.0.0 -m "Release inicial"
git tag -a v1.1.0 -m "Adiciona suporte a HTTPS"
git tag -a v1.1.1 -m "Corrige bug no ping DHCP"
git tag -a v2.0.0 -m "Refatoração completa"
```

---

## 📝 Mensagens de Commit (Conventional Commits)

Use prefixos para organizar melhor o histórico:

```bash
git commit -m "feat: adiciona novo recurso X"      # Nova funcionalidade
git commit -m "fix: corrige bug no ping"           # Correção de bug
git commit -m "docs: atualiza README"              # Documentação
git commit -m "refactor: reorganiza estrutura"     # Refatoração
git commit -m "perf: melhora performance do ping"  # Performance
git commit -m "style: ajusta formatação"           # Estilo/formatação
git commit -m "test: adiciona testes unitários"    # Testes
git commit -m "chore: atualiza dependências"       # Manutenção
```

---

## 🔍 Verificar Status do Build

### No GitHub:
1. Acesse: `https://github.com/SEU_USUARIO/mikrotik-routes/actions`
2. Clique no workflow "Build and Release Windows"
3. Veja o progresso em tempo real

### Via Linha de Comando (GitHub CLI):
```bash
# Instalar GitHub CLI (se não tiver)
winget install GitHub.cli

# Ver status dos workflows
gh run list

# Ver detalhes de um run específico
gh run view
```

---

## 📥 Baixar Releases

### Via Browser:
```
https://github.com/SEU_USUARIO/mikrotik-routes/releases
```

### Via GitHub CLI:
```bash
# Listar releases
gh release list

# Baixar última release
gh release download
```

---

## 🛠️ Comandos Úteis

### Desfazer último commit (mantém alterações):
```bash
git reset --soft HEAD~1
```

### Desfazer último commit (descarta alterações):
```bash
git reset --hard HEAD~1
```

### Ver histórico de commits:
```bash
git log --oneline --graph --decorate
```

### Deletar tag local e remota:
```bash
git tag -d v1.0.0                    # Local
git push origin --delete v1.0.0      # Remoto
```

### Atualizar tag existente:
```bash
git tag -fa v1.0.0 -m "Nova mensagem"
git push origin v1.0.0 --force
```

---

## 🐛 Troubleshooting

### Build falhou?
```bash
# Ver logs do último workflow
gh run view --log

# Re-executar workflow falhado
gh run rerun
```

### Commit sem querer?
```bash
# Desfazer último commit
git reset --soft HEAD~1

# Editar mensagem do último commit
git commit --amend -m "Nova mensagem"
```

### Esqueceu de adicionar arquivo?
```bash
git add arquivo_esquecido.py
git commit --amend --no-edit
git push --force
```

---

## 📚 Recursos Adicionais

- **Documentação do Workflow:** `.github/ACTIONS.md`
- **Exemplos de Badges:** `.github/BADGES.md`
- **Versionamento:** `.github/VERSION_EXAMPLE.txt`

---

*Dica: Adicione este arquivo aos favoritos para consulta rápida!*
