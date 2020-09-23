from nose.tools import *
from nose import SkipTest
from os.path import abspath, dirname, join, isfile
import os, sys
import wntr
import matplotlib.pylab as plt

testdir = dirname(abspath(str(__file__)))
test_datadir = join(testdir,'networks_for_testing')
ex_datadir = join(testdir,'..','..','examples','networks')

def test_plot_network1():
    filename = abspath(join(testdir, 'plot_network1.png'))
    if isfile(filename):
        os.remove(filename)
    
    inp_file = join(ex_datadir,'Net6.inp')
    wn = wntr.network.WaterNetworkModel(inp_file)
		
    plt.figure()
    wntr.graphics.plot_network(wn)
    plt.savefig(filename, format='png')
    plt.close()
    
    assert_true(isfile(filename))

def test_plot_interactive_network1():
    if (sys.version_info.major == 3) and (sys.version_info.minor == 4):
        raise SkipTest # skip if python version = 3.4
    filename = abspath(join(testdir, 'plot_interactive_network1.html'))
    if isfile(filename):
        os.remove(filename)
        
    inp_file = join(ex_datadir,'Net6.inp')
    wn = wntr.network.WaterNetworkModel(inp_file)
		
    plt.figure()
    wntr.graphics.plot_interactive_network(wn, filename=filename, auto_open=False)
    
    assert_true(isfile(filename))

def test_plot_fragility_curve1():
    from scipy.stats import lognorm
    filename = abspath(join(testdir, 'plot_fragility_curve1.png'))
    if isfile(filename):
        os.remove(filename)
        
    FC = wntr.scenario.FragilityCurve()
    FC.add_state('Minor', 1, {'Default': lognorm(0.5,scale=0.3)})
    FC.add_state('Major', 2, {'Default': lognorm(0.5,scale=0.7)}) 
    
    plt.figure()
    wntr.graphics.plot_fragility_curve(FC)
    plt.savefig(filename, format='png')
    plt.close()
    
    assert_true(isfile(filename))
    
def test_plot_tank_curve1():
    filename = abspath(join(testdir, 'plot_pump_curve1.png'))
    if isfile(filename):
        os.remove(filename)
        
    inp_file = join(ex_datadir,'Net3.inp')
    wn = wntr.network.WaterNetworkModel(inp_file)
    pump = wn.get_link('10')
    
    plt.figure()
    wntr.graphics.plot_pump_curve(pump)
    plt.savefig(filename, format='png')
    plt.close()
    
    assert_true(isfile(filename))

def test_custom_colormap():
    cmp = wntr.graphics.custom_colormap(numcolors=3, colors=['blue','white','red'], name='custom')
    assert_equal(cmp.N,3)
    assert_equal(cmp.name,'custom')
    
if __name__ == '__main__':
    cmp = test_custom_colormap()
    