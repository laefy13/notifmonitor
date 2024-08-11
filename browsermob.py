import subprocess
import argparse


def run_browsermob(dir):
    subprocess.Popen(
        ["java", "-jar", "browsermob-dist-2.1.4.jar", "--port", "9090"], cwd=dir
    )


if "__main__" == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=str,
        default=r"D:\DESKTOP\browsermob-proxy-2.1.4\lib",
        help="browsermob lib path",
    )
    args = parser.parse_args()
    try:
        run_browsermob(args.path)
    except Exception as e:
        print(f"Make sure that the --path is right")
