import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from q.agents.polyrelay import main


if __name__ == '__main__':
    try:
        asyncio.run(main(sys.argv))
    except KeyboardInterrupt:
        print('')