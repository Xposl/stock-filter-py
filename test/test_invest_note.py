import os
import sys
import pytest
from unittest import mock

# 假设 invest_note.py 在根目录下
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import invest_note

def test_help_command(capsys):
    test_args = ['invest_note.py', '-h']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '使用帮助' in captured.out

def test_update_ticker_list(capsys):
    test_args = ['invest_note.py', '-ticker']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '股票列表' in captured.out or '完成' in captured.out

def test_update_all_tickers(capsys):
    test_args = ['invest_note.py', '-all']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '更新' in captured.out or '完成' in captured.out

def test_update_prefix_tickers(capsys):
    test_args = ['invest_note.py', '-prefix', '60']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '更新' in captured.out or '完成' in captured.out

def test_analyze_stock_zh(capsys):
    test_args = ['invest_note.py', '-a', 'zh', '600000', '10']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '分析' in captured.out

def test_analyze_stock_hk(capsys):
    test_args = ['invest_note.py', '-a', 'hk', '00700', '10']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '分析' in captured.out

def test_analyze_stock_us(capsys):
    test_args = ['invest_note.py', '-a', 'us', 'AAPL', '10']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '分析' in captured.out

def test_analyze_on_time_zh(capsys):
    test_args = ['invest_note.py', '-ao', 'zh', '600000', '10']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '分时分析' in captured.out

def test_strategy_analyze_zh(capsys):
    test_args = ['invest_note.py', '-s', 'zh', '600000', '10']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '策略' in captured.out or '分析' in captured.out

def test_high_score_default(capsys):
    test_args = ['invest_note.py', '-hs']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '评分' in captured.out

def test_high_score_with_threshold(capsys):
    test_args = ['invest_note.py', '-hs', '80']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '评分' in captured.out

def test_high_score_export(capsys, tmp_path):
    out_file = tmp_path / 'high_score.json'
    test_args = ['invest_note.py', '-hs', '80', '-e', '-o', str(out_file)]
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    assert out_file.exists()

def test_export_high_score(capsys, tmp_path):
    out_file = tmp_path / 'export_high_score.json'
    test_args = ['invest_note.py', '-export-hs', '80', '-o', str(out_file)]
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    assert out_file.exists()

def test_unknown_command(capsys):
    test_args = ['invest_note.py', '-unknown']
    with mock.patch.object(sys, 'argv', test_args):
        invest_note.run_command_line_mode()
    captured = capsys.readouterr()
    assert '未知命令' in captured.out or 'help' in captured.out 