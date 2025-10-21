# 🤖 ArbitragemBot

Bot de **arbitragem automática** na **MEXC**, configurado para identificar oportunidades de *spread líquido* e executar operações de **três pernas simultâneas** dentro da mesma corretora.

## ⚙️ Funcionalidades principais

✅ **Varredura completa de paridades**
- Monitora todas as combinações possíveis de pares **/USDT**.  
- Exibe visualmente no Replit com bolinhas 🔴 (análise) e 🟢 (execução).

✅ **Leitura de saldo em tempo real**
- Mostra o saldo atualizado da sua conta **MEXC** diretamente no painel.  
- Atualiza a cada ciclo de busca.

✅ **Execução automática**
- Entra nas três pernas da arbitragem simultaneamente:  
  USDT → Moeda 1 → Moeda 2 → USDT  
- Considera taxas e calcula o **spread líquido** com precisão.

✅ **Relatório no Telegram**
- Envia mensagem automática ao concluir cada operação:  

📢 ARBITRAGEM EXECUTADA (MEXC)  
💱 Ciclo: USDT → Moeda 1 → Moeda 2 → USDT  
📊 Spread obtido: +X.XX%  
💰 Lucro líquido: +X.XX USDT  
🏦 Saldo atual: XXX.XX USDT  
🕒 Horário: HH:MM:SS  

## 🧠 Lógica de operação

O bot realiza arbitragem interna baseada na regra das **três pernas**:  
1. Compra o primeiro par (USDT → Moeda 1)  
2. Converte simultaneamente (Moeda 1 → Moeda 2)  
3. Retorna ao USDT (Moeda 2 → USDT)

Opera apenas quando o **spread líquido ≥ 0.5%**, conforme as configurações:

SPREAD_MIN = 0.5  
VOLUME_MIN = 800  
USE_BALANCE_PCT = 1.0  
TOTAL_FEE = 0.003  

## 🧩 Estrutura de arquivos

main.py — Arquivo principal que executa o bot  
arbitragem_bot.py — Lógica de arbitragem e execução das três pernas  
.replit — Configuração para execução no Replit  
.gitignore — Ignora chaves e arquivos sensíveis  
README.md — Este arquivo de descrição  

## 📬 Desenvolvido para:
MEXC — corretora principal de arbitragem interna (spot)

💡 Desenvolvimento personalizado por **Beatriz França**
