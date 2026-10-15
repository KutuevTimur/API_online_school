"""Guarded local-only maintenance. Dry-run by default; no filenames/secrets printed."""
import argparse
import asyncio
import json

from src.core.config import create_config
from src.modules.files.maintenance import LegacyFileMigration, OrphanReconciliation, require_local_maintenance


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('operation',choices=['migrate','reconcile'])
    parser.add_argument('--actor-user-id',type=int)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--allow-opaque-legacy',action='store_true',
                        help='Explicit synthetic-only import of old unparseable bytes as octet-stream attachments')
    parser.add_argument('--limit',type=int,default=100)
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error('limit must be 1..1000')
    config = create_config()
    require_local_maintenance(config)
    try:
        async with config.db_connection.session_local() as session:
            if args.operation == 'migrate':
                if args.actor_user_id is None:
                    parser.error('migrate requires an admin --actor-user-id')
                result = await LegacyFileMigration(session,config).run(args.actor_user_id,apply=args.apply,
                    limit=args.limit,allow_opaque=args.allow_opaque_legacy)
            else:
                result = await OrphanReconciliation(session,config).run(apply=args.apply)
            print(json.dumps(result))
    finally:
        await config.db_connection.engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
