import pstats
from pstats import SortKey

p = pstats.Stats("stats")
p.strip_dirs()
p.sort_stats(SortKey.TIME)
p.print_stats()
