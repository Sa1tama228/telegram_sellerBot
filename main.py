from aiogram.utils import executor
from utils.misc import dispatcher as dp
import handlers  # noqa: F401
from utils.rate_limiter import RateLimiter


dp.middleware.setup(RateLimiter(limit=15, timeout=10))

if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)