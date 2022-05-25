import argparse

from onlineconf import Config


def main():
    parser = argparse.ArgumentParser(description="Convert yaml config to cdb")
    parser.add_argument("yaml_file", help="Path to yaml config")
    parser.add_argument("cdb_file", help="Path to cdb config")
    args = parser.parse_args()

    conf = Config(args.cdb_file)
    conf.fill_from_yaml(args.yaml_file)


if __name__ == "__main__":
    main()
