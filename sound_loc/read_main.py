import numpy as np

Nmics = 64
Nsamp = 200

src = (0, 0)

pitch = 0.1
dist_per_samp = 0.1
C = 2.0

mics = []

obstacle = (3, -1)

def dist(src, pt, mic):
    d1 = ((src[1] - pt[1]) ** 2 + (src[0] - pt[0]) ** 2) ** 0.5
    d2 = ((mic[1] - pt[1]) ** 2 + (mic[0] - pt[0]) ** 2) ** 0.5
    return d1 + d2

mic_output = np.loadtxt("rx3.txt")
Nmics, Nsamp = mic_output.shape

for i in range(Nmics):
    mics.append((0, pitch * (-Nmics // 2 + 0.5 + i)))

graph_x = np.arange(Nsamp)

import matplotlib.pyplot as plt
import numpy as np

plt.style.use('_mpl-gallery')


colors = "bgrcm"

#for i in range(Nmics):
#    plt.plot(graph_x, mic_output[i] + 0.5 * i, c=colors[i % len(colors)], linewidth=3)
plt.imshow(mic_output, cmap="viridis")

plt.show()

reconst_img = np.zeros((Nmics, Nsamp))

for x in range(Nsamp):
    for y in range(Nmics):
        for mic_ind, mic in enumerate(mics):
            t_delay = round(dist(src, (dist_per_samp * x, pitch * (y - Nmics / 2 + 0.5)), mic) / dist_per_samp)
            if t_delay < Nsamp:
                reconst_img[y, x] += mic_output[mic_ind][t_delay]

plt.imshow(reconst_img, cmap="viridis")
plt.colorbar()
plt.show()
