from multiprocessing import Pool

import time;
def f(x):
    print(str(x) + ",", end="", flush=True);
    time.sleep(30);
    return x*x

k=1000;
if __name__ == '__main__':
    with Pool(k) as p:
        print(p.map(f, list(range(k))))
