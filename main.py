from os import getcwd
import argparse
from hmd import HApp

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Make dataset.")
    parser.add_argument('--scan', action=argparse.BooleanOptionalAction)
    parser.add_argument('--clean', action=argparse.BooleanOptionalAction)
    parser.add_argument('--delay', type=int, default=1)
    parser.add_argument('--page', type=int, default=200)
    parser.add_argument('--verbose', action=argparse.BooleanOptionalAction)
    args, _ = parser.parse_known_args()

    base_dir = getcwd()
    app = HApp(
        base_dir,
        scan=args.scan,
        clean=args.clean,
        delay_time=args.delay,
        max_page=args.page,
        verbose=args.verbose
    )
    app.setup()
    try:
        app.run()
    except KeyboardInterrupt as e:
        print(e)
        app.quit()
