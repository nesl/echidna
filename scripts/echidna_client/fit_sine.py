import numpy as np
import scipy.optimize as optimize
import scipy.fftpack as fftpack
import matplotlib.pyplot as plt
pi = np.pi
plt.figure(figsize = (15, 5))

# generate a perfect data set (my real data have tiny error)
def mysine(x, a1, a2, a3):
    return a1 * np.sin(a2 * x + a3)

N = 5000
xmax = 10
xReal = np.linspace(0, xmax, N)
a1 = 200.
a2 = 2*pi/10.5  # omega, 10.5 is the period
a3 = np.deg2rad(10.) # 10 degree phase offset
print(a1, a2, a3)
yReal = mysine(xReal, a1, a2, a3) + 0.2*np.random.normal(size=len(xReal))

yhat = fftpack.rfft(yReal)
idx = (yhat**2).argmax()
freqs = fftpack.rfftfreq(N, d = (xReal[1]-xReal[0])/(2*pi))
frequency = freqs[idx]

amplitude = yReal.max()
guess = [amplitude, frequency, 0.]
print(guess)
(amplitude, frequency, phase), pcov = optimize.curve_fit(
    mysine, xReal, yReal, guess)

period = 2*pi/frequency
print(amplitude, frequency, phase)

xx = xReal
yy = mysine(xx, amplitude, frequency, phase)
# plot the real data
plt.plot(xReal, yReal, 'r', label = 'Real Values')
plt.plot(xx, yy , label = 'fit')
plt.legend(shadow = True, fancybox = True)
plt.show()