# GitHub Actions - Build e Release Automático

Este repositório está configurado para gerar automaticamente releases do executável Windows a cada commit na branch `main` ou `master`.

## 🔄 Como Funciona

1. **Trigger**: A cada push na branch principal
2. **Build**: GitHub Actions compila o código Python em um executável `.exe` usando PyInstaller
3. **Release**: Cria automaticamente uma nova release com:
   - Tag versionada (formato: `vYYYY.MM.DD-HHmm-SHA`)
   - Executável `MikroTikRoutes.exe` anexado
   - Changelog baseado na mensagem do commit
   - Artefato de backup armazenado por 30 dias

## 📋 Configuração do Workflow

O arquivo `.github/workflows/build-and-release.yml` contém toda a configuração.

### Personalização

**Para fazer release apenas em tags (versões específicas):**
```yaml
on:
  push:
    tags:
      - 'v*'  # Apenas quando criar tags como v1.0.0, v2.1.3, etc.
```

**Para adicionar mais branches:**
```yaml
on:
  push:
    branches:
      - main
      - master
      - develop  # adicione aqui
```

## 🚀 Como Usar

### Método 1: Commit Normal (Automático)
```bash
git add .
git commit -m "feat: adiciona suporte a múltiplos gateways"
git push origin main
```
✅ Uma nova release será criada automaticamente!

### Método 2: Release com Tag (Manual)
```bash
# Criar tag versionada
git tag -a v1.0.0 -m "Versão 1.0.0 - Release inicial"
git push origin v1.0.0
```

## 📥 Download das Releases

As releases ficam disponíveis em:
```
https://github.com/SEU_USUARIO/mikrotik-routes/releases
```

Cada release contém:
- 📦 `MikroTikRoutes.exe` - Executável standalone para Windows
- 📝 Notas da versão com changelog
- ℹ️ Informações do commit e timestamp

## 🛠️ Build Local (Desenvolvimento)

Para testar o build localmente antes de fazer commit:
```bash
# Windows
.\scripts\build_exe.bat

# Ou manualmente
pip install pyinstaller
pyinstaller MikroTikRoutes.spec
```

## 🔍 Monitoramento

Para verificar o status do build:
1. Acesse a aba **Actions** no GitHub
2. Veja o workflow "Build and Release Windows"
3. Clique no commit específico para ver logs detalhados

## ⚙️ Requisitos

- Python 3.11 (configurado no workflow)
- Dependências listadas em `requirements.txt`
- Arquivo `app/assets/icon.ico` (ícone do executável)

## 🐛 Troubleshooting

**Build falhou?**
- Verifique os logs na aba Actions
- Confirme que `requirements.txt` está atualizado
- Verifique se o arquivo `icon.ico` existe

**Release não foi criada?**
- Confirme que você tem permissões de escrita no repositório
- Verifique se o branch está correto (main/master)
- Veja se há erros na etapa "Criar Release"

---

*Workflow configurado em: `.github/workflows/build-and-release.yml`*
