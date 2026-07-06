#!/usr/bin/env python3
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.prod_utils import summarize_and_index

def main():
    p = argparse.ArgumentParser(description='List JSON job definitions')
    p.add_argument('--jobdefs', required=True, help='Input jobdef JSON file')
    p.add_argument('--prod', action='store_true', help='Create SAM index definitions')
    args = p.parse_args()

    summarize_and_index(args.jobdefs, prod=args.prod)

if __name__ == '__main__':
    main()
