# CCC (Cline Claude Cost)

Ever wonder if you're overpaying for that $200/month Claude Max subscription? CCC analyzes your actual token usage from Cline VS Code extension logs to show you how much you would have paid if you were using Claude API calls instead. Discover your potential savings!

## 💰 Current Claude Pricing (per 1M tokens)

- **Input tokens**: $3.00
- **Output tokens**: $15.00  
- **Cache writes**: $3.75
- **Cache reads**: $0.30

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/jeremysltn/ccc.git
   cd ccc
   ```

2. **Install rich**
   ```bash
   pip install rich
   ```

3. **Run the calculator**
   ```bash
   python token_calculator.py
   ```

## 📁 Where it looks

The script analyzes logs from:
```
~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks/
```

Each Cline project folder contains a `ui_messages.json` file with detailed usage data.

## 📊 Sample Output

```
SUMMARY:
Files processed: 25
Entries processed: 147
Total tokensIn: 1,250,000
Total tokensOut: 850,000
Total cacheWrites: 125,000
Total cacheReads: 300,000

COST BREAKDOWN (per 1M tokens/operations):
Input tokens: 1,250,000 × $3.00/1M = $3.7500
Output tokens: 850,000 × $15.00/1M = $12.7500
Cache writes: 125,000 × $3.75/1M = $0.4688
Cache reads: 300,000 × $0.30/1M = $0.0900
Calculated total cost: $17.0588

USAGE PERIOD:
Date range: 2025-01-15 to 2025-01-24
Time span: 9 days
📊 Estimated monthly average: $56.86

📈 DAILY USAGE ANALYSIS:
Active coding days: 7
Average daily cost: $2.44
Peak daily cost: $8.45
Average daily tokens: 162,500
Peak daily tokens: 425,000
Average daily API calls: 21.0
Peak daily API calls: 67
Daily cost variation: 246.3% (peak vs average)

ADDITIONAL STATS:
Average tokens per API call: 14,285.7
Average cost per API call: $0.1161
```

## 🛠️ Requirements

- Python 3.6+
- VS Code with Cline extension installed
- Some coding history with Cline (the more usage, the more accurate the estimates)

## ⚠️ Important Notes

- API pricing subject to change. Check [Anthropic's official pricing](https://www.anthropic.com/pricing) for current rates.
- *Usage limits not included* - Claude Max subscription plans have undisclosed usage limits

## 🤝 Contributing

Found a bug or want to add a feature? Pull requests welcome!

## 📝 License

MIT License - feel free to use and modify as needed.
