"""Recalcula em Python, de forma independente, os números do painel de duplicidades de descontos.

Uso:
    python tests/conferir_totais.py <pasta>
    python tests/conferir_totais.py --desc desconto.xlsx --cad Cadastro_Interior.xlsx Cadastro_Leste.xlsx

Com <pasta>, segue a mesma regra do painel: o xlsx mais recente (data de modificação) da subpasta
Descontos e todos os xlsx da subpasta Cadastro. Opcional: --sup Interior (ou Leste) para filtrar.
Requer pandas e openpyxl.
"""
import argparse
import os
import sys
import unicodedata

import pandas as pd


def norm(s):
    s = unicodedata.normalize('NFD', str(s)).encode('ascii', 'ignore').decode()
    return '_'.join(s.strip().upper().split())


def sup_nome(s):
    n = norm(s)
    if n in ('LAGOS', 'INTERIOR'):
        return 'Interior'
    if n == 'LESTE':
        return 'Leste'
    return str(s).strip().capitalize()


def arquivos_da_pasta(pasta):
    desc, cad = [], []
    for raiz, _, nomes in os.walk(pasta):
        partes = [norm(p) for p in os.path.relpath(raiz, pasta).split(os.sep)]
        for n in nomes:
            if not n.lower().endswith('.xlsx') or n.startswith('~$'):
                continue
            c = os.path.join(raiz, n)
            if 'DESCONTOS' in partes:
                desc.append(c)
            elif 'CADASTRO' in partes:
                cad.append(c)
    desc.sort(key=os.path.getmtime, reverse=True)
    return desc[:1], cad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pasta', nargs='?')
    ap.add_argument('--desc')
    ap.add_argument('--cad', nargs='*', default=[])
    ap.add_argument('--sup')
    a = ap.parse_args()
    if a.pasta:
        desc, cad = arquivos_da_pasta(a.pasta)
    else:
        desc, cad = [a.desc], a.cad
    if not desc or not desc[0] or not cad:
        sys.exit('Informe a pasta ou --desc e --cad.')

    df = pd.read_excel(desc[0])
    df.columns = [norm(c) for c in df.columns]
    hora = df['DAT_ACESSO_HORA'].astype(str).str.slice(0, 8) if 'DAT_ACESSO_HORA' in df else '00:00:00'
    df['DT'] = pd.to_datetime(pd.to_datetime(df['DAT_ACESSO']).dt.strftime('%Y-%m-%d') + ' ' + hora)
    df['REF'] = pd.to_datetime(df['REFERENCIA']).dt.strftime('%Y-%m')
    df['CHAVE'] = df['EMP_CODIGO'].astype(int).astype(str) + '-' + df['NUM_LIGACAO'].fillna(0).astype('int64').astype(str)

    partes = []
    for f in cad:
        c = pd.read_excel(f)
        c.columns = [norm(x) for x in c.columns]
        if 'CHAVE_LIGACAO' not in c:
            c['CHAVE_LIGACAO'] = '*-' + c['NUM_LIGACAO'].astype('int64').astype(str)
        partes.append(c[['CHAVE_LIGACAO', 'CIDADE', 'SUPERINTENDENCIA']])
    cadastro = pd.concat(partes).drop_duplicates('CHAVE_LIGACAO', keep='last').set_index('CHAVE_LIGACAO')
    df['SUP'] = df['CHAVE'].map(cadastro['SUPERINTENDENCIA']).map(lambda s: sup_nome(s) if pd.notna(s) else None)

    total = len(df)
    sem_valor = df['DESCONTO'].isna() | df['VALOR_TOTAL'].isna()
    mat0 = ~sem_valor & ~(df['NUM_LIGACAO'] > 0)
    zero = ~sem_valor & ~mat0 & ~(df['DESCONTO'] > 0)
    valido = ~sem_valor & ~mat0 & ~zero
    fora = valido & df['SUP'].isna()
    base = df[valido & df['SUP'].notna()].copy()
    print(f'Arquivo de descontos: {os.path.basename(desc[0])}')
    print(f'Linhas: {total:,} | sem valores {sem_valor.sum()} | matrícula 0 {mat0.sum()} | desconto zero {zero.sum()} '
          f'| fora das superintendências {fora.sum():,} (R$ {df.loc[fora, "DESCONTO"].sum():,.2f}) | base {len(base):,}')
    if a.sup:
        base = base[base['SUP'] == a.sup]
        print(f'Filtro: {a.sup}')

    base['C'] = (base['DESCONTO'] * 100).round().astype('int64')
    base['T'] = (base['VALOR_TOTAL'] * 100).round().astype('int64')
    base = base.sort_values(['DT', 'NUM_LOG'])

    print(f'\nLançamentos analisados: {len(base):,} | R$ {base["DESCONTO"].sum():,.2f} | matrículas {base["NUM_LIGACAO"].nunique():,}')
    g = base.groupby(['NUM_LIGACAO', 'REF', 'C']).agg(n=('NUM_LOG', 'size'), nt=('T', 'nunique'), desc=('DESCONTO', 'first'))
    g = g[g.n > 1].copy()
    g['nivel'] = g.nt.map(lambda x: 1 if x == 1 else 2)
    g['rep'] = g.n - 1
    g['val'] = g.rep * g.desc
    mats = g.reset_index()['NUM_LIGACAO'].nunique()
    print(f'Matrículas com duplicidade: {mats:,}')
    print(f'Lançamentos a mais: {int(g.rep.sum()):,} em {len(g):,} descontos repetidos')
    print(f'Valor registrado em duplicidade: R$ {g.val.sum():,.2f}')
    for n in (1, 2):
        x = g[g.nivel == n]
        print(f'  Nível {n}: {len(x):,} descontos repetidos, {int(x.rep.sum()):,} lançamentos a mais, R$ {x.val.sum():,.2f}')

    al = base.groupby(['NUM_LIGACAO', 'C']).agg(nr=('REF', 'nunique'))
    al = al[al.nr > 1]
    print(f'Alerta entre meses: {len(al):,} descontos, {al.reset_index()["NUM_LIGACAO"].nunique():,} matrículas')

    ve = base.groupby(['NUM_LIGACAO', 'REF']).agg(nd=('C', 'nunique'))
    ve = ve[ve.nd > 1]
    print(f'A verificar: {ve.reset_index()["NUM_LIGACAO"].nunique():,} matrículas, {len(ve):,} combinações de matrícula e mês')

    print('\nPor mês (lançamentos a mais: nível 1 / nível 2 / total / R$):')
    gm = g.reset_index().groupby(['REF', 'nivel']).agg(rep=('rep', 'sum'), val=('val', 'sum')).unstack(fill_value=0)
    for ref, r in gm.iterrows():
        r1, r2 = int(r[('rep', 1)]) if ('rep', 1) in r else 0, int(r[('rep', 2)]) if ('rep', 2) in r else 0
        v = r['val'].sum()
        print(f'  {ref}: {r1:>4} / {r2:>4} / {r1 + r2:>4} / R$ {v:,.2f}')


if __name__ == '__main__':
    main()
