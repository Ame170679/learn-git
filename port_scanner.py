import socket
import sys
import argparse  # 新增：支持命令行参数
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_port(ip: str, port: int, timeout: float = 0.5) -> tuple[int, bool]:
    """检测指定IP的指定端口是否开放"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            return (port, result == 0)
    except (socket.timeout, ConnectionRefusedError):
        return (port, False)
    except Exception as e:
        print(f"⚠️  端口{port}检测异常: {str(e)}", file=sys.stderr)
        return (port, False)

def port_scanner(
    target_ip: str,
    start_port: int = 1,
    end_port: int = 65535,
    max_workers: int = 100,
    timeout: float = 0.5
) -> list[int]:
    """批量扫描指定IP的端口范围，返回开放的端口列表"""
    open_ports = []
    total_ports = end_port - start_port + 1
    completed = 0

    print(f"🚀 开始扫描 IP: {target_ip} | 端口范围: {start_port}-{end_port} | 线程数: {max_workers}")
    print("-" * 60)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_port = {
            executor.submit(scan_port, target_ip, port, timeout): port
            for port in range(start_port, end_port + 1)
        }

        for future in as_completed(future_to_port):
            port, is_open = future.result()
            completed += 1
            if completed % 100 == 0 or completed == total_ports:
                progress = (completed / total_ports) * 100
                print(f"\r📊 进度: {completed}/{total_ports} ({progress:.1f}%)", end="", flush=True)

            if is_open:
                open_ports.append(port)
                print(f"\n✅ 发现开放端口: {port}", flush=True)

    print("\n" + "-" * 60)
    return sorted(open_ports)

if __name__ == "__main__":
    # 新增：命令行参数解析（替代硬编码，方便GitHub Actions传参）
    parser = argparse.ArgumentParser(description="GitHub Actions 端口扫描脚本")
    parser.add_argument("--ip", required=True, help="目标IP地址（必填）")
    parser.add_argument("--start-port", type=int, default=1, help="起始端口，默认1")
    parser.add_argument("--end-port", type=int, default=1000, help="结束端口，默认1000")
    parser.add_argument("--workers", type=int, default=100, help="线程数，默认100")
    parser.add_argument("--timeout", type=float, default=0.5, help="超时时间，默认0.5秒")
    args = parser.parse_args()

    # 用命令行参数替代硬编码
    TARGET_IP = args.ip
    START_PORT = args.start_port
    END_PORT = args.end_port
    MAX_WORKERS = args.workers
    TIMEOUT = args.timeout

    try:
        open_ports = port_scanner(TARGET_IP, START_PORT, END_PORT, MAX_WORKERS, TIMEOUT)

        if open_ports:
            print(f"🎉 扫描完成！IP {TARGET_IP} 开放的端口列表:")
            print(f"开放端口: {', '.join(map(str, open_ports))}")
            # 新增：将结果写入文件，方便下载
            with open("open_ports.txt", "w") as f:
                f.write(f"目标IP: {TARGET_IP}\n")
                f.write(f"扫描范围: {START_PORT}-{END_PORT}\n")
                f.write(f"开放端口: {', '.join(map(str, open_ports))}\n")
        else:
            print(f"❌ 扫描完成！IP {TARGET_IP} 在 {START_PORT}-{END_PORT} 范围内未发现开放端口")
            with open("open_ports.txt", "w") as f:
                f.write(f"目标IP: {TARGET_IP}\n")
                f.write(f"扫描范围: {START_PORT}-{END_PORT}\n")
                f.write("开放端口: 无\n")
    except KeyboardInterrupt:
        print("\n⚠️  用户中断扫描，程序退出")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 扫描出错: {str(e)}", file=sys.stderr)
        sys.exit(1)