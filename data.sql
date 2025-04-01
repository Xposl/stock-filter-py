



SELECT
    strategy_id AS id,
    round(SUM(net_profit)/1000)/100 AS net_profit,
    round(SUM(gross_profit)/1000)/100 AS gross_profit,
    round(SUM(gross_loss)/1000)/100 AS gross_loss,
    round(SUM(gross_profit)/1000/SUM(win_trades))/100 AS avg_win,
    round(SUM(gross_loss)/1000/SUM(loss_trades))/100 AS avg_loss,
    SUM(trades) AS trades,
    SUM(win_trades) AS win_trades,
    SUM(loss_trades) AS loss_trades,
    SUM(win_trades)/SUM(trades) * 100 AS profitable
FROM project_strategy
GROUP BY strategy_id