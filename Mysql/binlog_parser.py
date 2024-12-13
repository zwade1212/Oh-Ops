import re
from datetime import datetime
import argparse
import sys

"""
参考my2sql项目, 离线解析 mysqlbinlog --base64-output=decode-rows -vv 的输出，记录事务开始时间与提交时间等信息，并筛选符合条件的大事务
"""

def parse_binlog(file_path=None):
    """解析 mysqlbinlog 的输出，记录事务开始时间与提交时间"""
    transactions = []
    current_transaction = None
    commit_str = 0  # 标记事务是否已提交

    # 支持标准输入
    if file_path:
        file = open(file_path, 'r')
    else:
        file = sys.stdin

    for line in file:
        line = line.strip()

        # 获取事务的逻辑开始时间
        if line.startswith("SET TIMESTAMP="):
            start_timestamp = int(line.split("=")[1].strip("/*!*/;"))
            if current_transaction:
                transactions.append(current_transaction)
            current_transaction = {
                "tables": {},
                "start_time": datetime.fromtimestamp(start_timestamp),
                "stop_time": None,
                "start_pos": None,
                "stop_pos": None,
                "rows": 0,
                "duration": 0,
            }

        # 捕获start_pos 或者 stop_pos
        if line.startswith("# at "):
            current_position = int(line.split()[2])
            if current_transaction and current_transaction["start_pos"] is None:
                current_transaction["start_pos"] = current_position
            elif current_transaction and commit_str:
                current_transaction["stop_pos"] = current_position

        # 捕获表操作
        if line.startswith("### INSERT") or line.startswith("### UPDATE") or line.startswith("### DELETE"):
            operation = line.split()[1]
            match = re.search(r"`(.+?)`\.`(.+?)`", line)
            if match and current_transaction:
                db_table = f"{match.group(1)}.{match.group(2)}"
                if db_table not in current_transaction["tables"]:
                    current_transaction["tables"][db_table] = {"inserts": 0, "updates": 0, "deletes": 0}
                current_transaction["tables"][db_table][f"{operation.lower()}s"] += 1
                current_transaction["rows"] += 1

        # 捕获事务结束
        if line.startswith("COMMIT"):
            commit_str = 1  # 标记事务已提交

        # 获取事务的提交时间
        if line.startswith("# original_commit_timestamp="):
            if current_transaction:
                pattern = r"\((.*?)\)"
                timestamp = re.search(pattern, line)
                if timestamp:
                    stop_time = datetime.strptime(
                        timestamp.group(1), "%Y-%m-%d %H:%M:%S.%f CST"
                    )
                    current_transaction["stop_time"] = stop_time
                    current_transaction["duration"] = (
                        (stop_time - current_transaction["start_time"]).total_seconds()
                    )
                    transactions.append(current_transaction)
                    current_transaction = None
                    commit_str = 0  

    # 添加最后一个事务（如果未完成）
    if current_transaction:
        transactions.append(current_transaction)

    if file_path:
        file.close()
    return transactions


def filter_transactions(transactions, long_trx_seconds, big_trx_row_limit, startpos=None, stoppos=None, starttime=None, stoptime=None):
    """筛选符合条件的事务"""
    filtered = []
    for trx in transactions:
        if (trx["duration"] >= long_trx_seconds or trx["rows"] >= big_trx_row_limit) and \
           (startpos is None or trx["start_pos"] >= startpos) and \
           (stoppos is None or trx["stop_pos"] <= stoppos) and \
           (starttime is None or trx["start_time"] >= starttime) and \
           (stoptime is None or trx["stop_time"] <= stoptime):
            filtered.append(trx)
    return filtered


def format_transactions(transactions):
    """格式化事务输出"""
    output = []  
    for trx in transactions:
        tables = [
            f"{table}(inserts={changes['inserts']}, updates={changes['updates']}, deletes={changes['deletes']})"
            for table, changes in trx["tables"].items()
        ]
        output.append(
            f"{trx['start_time']} {trx['stop_time']} {trx['start_pos']} {trx['stop_pos']} "
            f"{trx['rows']} {trx['duration']} [{' '.join(tables)}]"
        )
    return output


def main():
    parser = argparse.ArgumentParser(description="Parse MySQL binlog for long or big transactions with filtering options.")
    parser.add_argument("--file", help="Path to the binlog file parsed with mysqlbinlog. If omitted, read from stdin.")
    parser.add_argument("--long-trx-seconds", type=int, default=10, help="Threshold for long transaction duration.")
    parser.add_argument("--big-trx-row-limit", type=int, default=100, help="Threshold for big transaction row count.")
    parser.add_argument("--startpos", type=int, help="Filter transactions starting from this position.")
    parser.add_argument("--stoppos", type=int, help="Filter transactions ending at or before this position.")
    parser.add_argument("--starttime", type=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S"), help="Filter transactions starting from this time (YYYY-MM-DD HH:MM:SS).")
    parser.add_argument("--stoptime", type=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S"), help="Filter transactions ending at or before this time (YYYY-MM-DD HH:MM:SS).")

    args = parser.parse_args()
    transactions = parse_binlog(args.file)
    filtered_transactions = filter_transactions(transactions, args.long_trx_seconds, args.big_trx_row_limit, args.startpos, args.stoppos, args.starttime, args.stoptime)
    output = format_transactions(filtered_transactions)

    # 输出结果
    print(f"starttime stoptime startpos stoppos rows duration tables")
    for line in output:
        print(line)


if __name__ == "__main__":
    main()