from os import getcwd
import argparse
from datetime import datetime
from hmd import HApp

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Make dataset.")
    parser.add_argument('--scan', action=argparse.BooleanOptionalAction)
    parser.add_argument('--clean', action=argparse.BooleanOptionalAction)
    parser.add_argument('--delay', type=int, default=1)
    parser.add_argument('--days', type=int, default=365)
    parser.add_argument('--from_date', type=str, default=datetime.now().strftime("%d_%m_%Y"))
    parser.add_argument('--verbose', action=argparse.BooleanOptionalAction)
    args, _ = parser.parse_known_args()

    base_dir = getcwd()

    app = HApp(
        base_dir,
        scan=args.scan,
        clean=args.clean,
        delay_time=args.delay,
        from_date=args.from_date,
        days=args.days,
        verbose=args.verbose
    )
    app.setup()
    try:
        app.run()
    except KeyboardInterrupt as e:
        print(e)
        app.quit()
