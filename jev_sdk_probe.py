#!/usr/bin/env python3
"""Official-SDK Jev access check. Offline by default, one billable call with --live."""
from __future__ import annotations
import argparse
import os
from jev_bridge import JevClient, JevError, RUBRIC, RUBRIC_INSTRUCTIONS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='send exactly one potentially billable SDK POST')
    args = parser.parse_args()
    selected = 'TYPESAFE_API_KEY' if os.getenv('TYPESAFE_API_KEY') else 'JEV_API_KEY'
    key = os.getenv('TYPESAFE_API_KEY') or os.getenv('JEV_API_KEY', '')
    model = os.getenv('JEV_MODEL', 'jev-1.13.0')
    print('Selected key:', selected if key else 'NONE', '(key is never displayed)')
    print('Model:', model)
    print('SDK:', 'typesafe-sdk>=0.7.0; automatic HTTP retries disabled')
    if not args.live:
        print('Offline only. Add --live to authorize ONE potentially billable scoring call.')
        return 0
    if not key:
        print('Missing API key.'); return 2
    client = None
    try:
        client = JevClient(key, model)
        output = client.decide(
            {'fixed_prompt': 'def ', 'continuation': 'add(a, b): return a + b'},
            {'quality': {'type': 'score', 'instructions': RUBRIC_INSTRUCTIONS,
                         'criteria': RUBRIC}},
        )
        print('SUCCESS: resolved_model=', client._resolved_model,
              ' normalized_score=', output['quality']['score'] / (len(RUBRIC)-1),
              ' successful_requests=', client.requests)
        if client.cost > 0:
            print('Provider-reported cost (USD):', client.cost)
        else:
            print('Provider-reported cost: unavailable/zero (NOT proof of free usage)')
        return 0
    except JevError as exc:
        print('FAILED:', exc)
        print('If HTTP 403 persists, contact TypeSafe with the request ID; SDK cannot override Cloudflare.')
        return 2
    finally:
        if client is not None:
            client.close()


if __name__ == '__main__':
    raise SystemExit(main())
