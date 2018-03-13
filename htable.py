#!/usr/bin/env python

'''
Oh dear. Why have you come in here? No good code awaits you, only an ugly hack.

Given a table-like object, covert it into a H table. The "latex" tablefmt
available from 0.7 of tabulate doesn't give enough flexibility to work with, so
that's a no go.

Usage: See if __name__ == '__main__'.
'''

import re
import numpy
import tabulate
import collections


LATEX_CONV = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '<': r'\textless ',
    '>': r'\textgreater ',
}
LATEX_RGX = re.compile('|'.join(
    re.escape(key)
    for key in sorted(LATEX_CONV.keys(), key=lambda item: - len(item))
))


def tex_escape(text):
    return LATEX_RGX.sub(lambda match: LATEX_CONV[match.group()], text)


def htable(data, caption=None, first_row_header=True, first_col_header=True, grey_idxs=(), grey_styles=(r'\cellcolor{gray!25}', r'\bfseries{}'), numdec=None):
    tsv = tabulate.tabulate(data, tablefmt="tsv")
    out_lines = [r'\begin{table}[H]', r'\centering']

    if caption is not None:
        out_lines.append(r'\caption{%s}' % tex_escape(caption))

    num_cols = tsv.split('\n', 1)[0].count('\t') + 1

    tabular_cols = '|' + '|'.join(['l'] * num_cols) + '|'

    out_lines.append(r'\begin{tabular}{%s}' % tabular_cols)
    out_lines.append(r'\hline')

    tsv_lines = tsv.split('\n')

    try:
        import pandas
    except ImportError:
        pass
    else:
        # Add DF header
        if isinstance(data, pandas.DataFrame):
            tsv_lines.insert(0, '\t' + '\t'.join(map(str, data.columns.values)))

    for row_i, row in enumerate(tsv_lines):
        if not row:
            continue

        cur_line = []

        cols = row.split('\t')

        if len(cols) != num_cols:
            raise ValueError(
                "Number of cols changed from {} to {}".format(
                    num_cols, len(cols),
                )
            )

        cols_to_grey = collections.defaultdict(list)

        if not first_col_header or row_i != 0:
            for grey_style_idx, grey_idx in enumerate(grey_idxs):
                try:
                    compare_to = float(cols[grey_idx])
                except ValueError:
                    # Skip this row, grey_idx is unusable
                    continue

                for i, col in enumerate(cols):
                    try:
                        if float(col) < compare_to:
                            cols_to_grey[i].append(grey_style_idx)
                    except ValueError:
                        # Skip this column, not usable
                        continue

        colfmt = "%.{}f".format(numdec)

        for col_i, col in enumerate(cols):
            col = col.strip()

            if numdec:
                try:
                    col = colfmt % float(col)
                except ValueError:
                    pass

            col = tex_escape(col)

            if col:
                if (row_i == 0 and first_row_header) or \
                   (col_i == 0 and first_col_header):
                    cur_line.append(r'\textbf{%s}' % col)
                else:
                    if col_i in cols_to_grey:
                        styles = ''
                        for style_idx in cols_to_grey[col_i]:
                            styles += grey_styles[style_idx]
                        cur_line.append(r'%s%s' % (styles, col))
                    else:
                        cur_line.append(col)
            else:
                cur_line.append('~')

        out_lines.append(' & '.join(cur_line) + r' \\ \hline')

    out_lines.append(r'\end{tabular}')
    out_lines.append(r'\end{table}')

    return '\n'.join(out_lines) + '\n'


if __name__ == '__main__':
    # Lightweight testing.
    import numpy
    x = numpy.array([
        ['', '95% VaR', '99% VaR', '97.5% ES'],
        ['Merged PDF', -0.020, -0.038, -0.041],
        ['KDE', -0.019, -0.037, -0.040]
    ])
    print(htable(x, caption='Foo % bar', first_col_header=True))

    import pandas
    y = pandas.DataFrame(numpy.random.randint(low=0, high=10, size=(5, 5)),
                         columns=['a', 'b', 'c', 'd', 'e'])
    print(htable(y, first_col_header=True))

    y = pandas.DataFrame(numpy.random.randint(low=0, high=10, size=(5, 5)))
    print(htable(y, first_col_header=True))

    y = pandas.DataFrame(numpy.random.randint(low=0, high=10, size=(5, 5)))
    y[2][2] = 'testing'
    print(htable(y, first_col_header=True, grey_idxs=[2, 4]))

    y = pandas.DataFrame(numpy.random.uniform(low=0, high=10, size=(5, 5)))
    y[2][2] = 'testing'
    print(htable(y, first_col_header=True, numdec=2))
