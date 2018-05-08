import matplotlib.pyplot as plt


def table_9(shortest8, ecmp8, ecmp64):
    shortest8 = sorted(shortest8.values())
    ecmp8 = sorted(ecmp8.values())
    ecmp64 = sorted(ecmp64.values())
    plt.plot(shortest8)
    plt.plot(ecmp8)
    plt.plot(ecmp64)
    plt.ylabel('# Distinct Paths Link is on')
    plt.xlabel('Rank of Link')
    plt.legend(['8 Shortest Paths', '8-Way ECMP', '64-Way ECMP'], loc='upper left')
    plt.savefig('figure_9.png')
    
