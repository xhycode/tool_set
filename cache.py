import os
import debug


class Cache():
    def __init__(self, path=None, fname="out", clear=False):
        if os.path.exists(path):
            curdir = path
        else:
            curdir = os.getcwd()
        self._outdir = os.path.join(curdir, 'cache')
        if not os.path.exists(self._outdir):
            print("creating cache dir")
            os.mkdir(self._outdir)
        self.outfile = os.path.join(self._outdir, fname + ".txt")
        if clear:
            self.clear()


    def write(self, data, end='\n'):
        try:
            if not os.path.isfile(self.outfile):
                fd = open(self.outfile, mode="w")
                fd.close()
            with open(self.outfile, "a+") as fd:
                fd.write(data + end)
                fd.close()
        except:
            debug.info_ln(self.outfile + ' 写失败')


    def write_lines(self, data, enter=True):
        with open(self.outfile, "a+") as fd:
            for d in data:
                if enter:
                    fd.write(d + '\n')
                else:
                    fd.write(d)
            fd.close()


    def readlines(self):
        if not os.path.isfile(self.outfile):
            return ""
        else:
            fd = open(self.outfile, mode="r")
            ret = fd.readlines()
            fd.close()
            return ret

    def clear(self):
        with open(self.outfile, 'w') as fd:
                fd.close()

