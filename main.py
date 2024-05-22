from os import getcwd
import argparse
from hmd import HApp

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Make dataset.")
    parser.add_argument('--scan', action=argparse.BooleanOptionalAction)
    parser.add_argument('--clean', action=argparse.BooleanOptionalAction)
    args, _ = parser.parse_known_args()

    base_dir = getcwd()
    app = HApp(base_dir, args.scan, args.clean)
    app.setup()
    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()
