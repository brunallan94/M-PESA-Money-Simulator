from tqdm import tqdm
import time


# Testing different progress bars
def using_tqdm_module():
    for i in tqdm(range(5_000), disable=False, desc='Loading...', ncols=75):
        time.sleep(0.01)

    print('Loading Completed...')


if __name__ == '__main__':
    using_tqdm_module()