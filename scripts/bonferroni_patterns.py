"""
Bonferroni-corrected pattern significance table
------------------------------------------------
Reads your pattern results, applies Bonferroni correction,
and outputs:
  1. Full table with correction columns (CSV)
  2. Significant-only table (CSV)
  3. Pretty summary printed to console

Usage:
    python bonferroni_patterns.py
    python bonferroni_patterns.py --input my_results.tsv --alpha 0.05 --min-q 5
"""

import csv
import argparse
import sys
from io import StringIO

# ── helpers ──────────────────────────────────────────────────────────────────

def phi_label(phi):
    phi = abs(phi)
    if phi >= 0.5:  return "strong"
    if phi >= 0.3:  return "moderate"
    if phi >= 0.1:  return "weak"
    return "negligible"

def verdict(p_raw, p_bonf_threshold, phi, p_q_occs, min_q):
    """Return a reliability verdict for one pattern."""
    if p_q_occs < min_q:
        return "LOW N"
    #print(f"p_raw={p_raw}, p_bonf_threshold={p_bonf_threshold}, phi={phi}, p_q_occs={p_q_occs}, min_q={min_q}", file=sys.stderr)
    sig = p_raw < p_bonf_threshold
    eff = abs(phi)
    if sig and eff >= 0.5:  return "STRONG"
    if sig and eff >= 0.3:  return "MODERATE"
    if sig and eff >= 0.1:  return "WEAK"
    if sig:                 return "SIG / tiny effect"
    if eff >= 0.3:          return "EFFECT / not sig"
    return "NOT SIGNIFICANT"

def direction(decision, precision):
    """Positive trigger (promotes pattern) vs negative (suppresses it)."""
    if decision.strip().lower() == "yes":
        return "period-specific"
    return "positive" if float(precision) < 90 else "negative"

# ── embedded data (paste your TSV here if not loading from file) ─────────────

EMBEDDED_DATA = """\
Pattern\tPeriod Predictor\tp_occs\tp_q_occs\tDecision\tCoef\tCoverage\tPrecision\tG-statistic\tp-value\tCramers_phi
node:X:prev:upos=PRON,node:X:own:Mood=Ind,node:X:prev:Gender=Com\tNo\t14\t9\tyes\t0.169\t27.273\t64.286\t46.113\t0\t1.815
node:X:prev:upos=SCONJ,node:X:child:rel_shallow=mark\tNo\t5\t3\tyes\t0.764\t9.091\t60\t14.743\t0\t1.717
node:X:child:upos=SCONJ,node:X:prev:upos=PRON,node:X:own:Mood=Ind\tNo\t15\t9\tyes\t0.171\t27.273\t60\t44.23\t0\t1.717
node:X:child:upos=SCONJ,node:X:prev:upos=PRON,node:X:prev:Gender=Com\tNo\t18\t9\tyes\t0.043\t27.273\t50\t39.64\t0\t1.484
node:X:child:Gender=Com,node:X:child:upos=INTJ,node:CLH:own:Voice=Act\tNo\t6\t3\tyes\t0.696\t9.091\t50\t13.213\t0\t1.484
node:CLH:own:rel_shallow=root,node:X:child:PronType=Prs,node:X:prev:Definite=Def\tNo\t25\t12\tyes\t0.09\t36.364\t48\t51.565\t0\t1.436
node:X:child:upos=PRON,node:CLH:own:rel_shallow=root,node:X:prev:Definite=Def\tNo\t25\t12\tyes\t0.527\t36.364\t48\t51.565\t0\t1.436
node:X:child:Gender=Com,node:X:prev:upos=PRON,node:CLH:own:upos=VERB\tNo\t23\t11\tyes\t0.173\t33.333\t47.826\t47.164\t0\t1.432
node:X:prev:upos=PRON,node:X:prev:Gender=Com\tNo\t27\t12\tyes\t0.099\t36.364\t44.444\t49.202\t0\t1.35
node:X:child:upos=PRON,node:X:prev:upos=PRON,node:X:prev:Gender=Com\tNo\t27\t12\tyes\t0.028\t36.364\t44.444\t49.202\t0\t1.35
node:X:child:Gender=Com,node:X:prev:upos=PRON,node:X:prev:Gender=Com\tNo\t27\t12\tyes\t0.405\t36.364\t44.444\t49.202\t0\t1.35
node:X:prev:Case=Nom,node:CLH:own:rel_shallow=root,node:X:prev:Definite=Def\tNo\t27\t12\tyes\t0.32\t36.364\t44.444\t49.202\t0\t1.35
node:X:child:Definite=Def,node:CLH:own:rel_shallow=root,node:X:prev:Definite=Def\tNo\t31\t13\tyes\t0.074\t39.394\t41.935\t51.425\t0\t1.288
node:X:child:Gender=Com,node:X:child:upos=PRON,node:X:prev:upos=PRON\tNo\t32\t13\tyes\t0.157\t39.394\t40.625\t50.418\t0\t1.255
node:X:child:upos=PRON,node:X:prev:upos=PRON,node:X:child:Case=Nom\tNo\t32\t13\tyes\t0.579\t39.394\t40.625\t50.418\t0\t1.255
node:CLH:own:rel_shallow=root,node:X:prev:Definite=Def\tNo\t32\t13\tyes\t0.07\t39.394\t40.625\t50.418\t0\t1.255
node:CLH:own:rel_shallow=root,node:X:child:Case=Nom,node:X:prev:Definite=Def\tNo\t32\t13\tyes\t0.024\t39.394\t40.625\t50.418\t0\t1.255
node:X:prev:upos=PRON,node:X:child:Case=Nom\tNo\t33\t13\tyes\t0.033\t39.394\t39.394\t49.454\t0\t1.224
node:X:child:Gender=Com,node:X:prev:upos=PRON\tNo\t33\t13\tyes\t0.068\t39.394\t39.394\t49.454\t0\t1.224
node:X:child:Gender=Com,node:X:prev:upos=PRON,node:Y:own:has_child=No\tNo\t33\t13\tyes\t0.023\t39.394\t39.394\t49.454\t0\t1.224
node:X:child:upos=PRON,node:X:prev:upos=PRON,node:Y:own:has_child=No\tNo\t33\t13\tyes\t0.152\t39.394\t39.394\t49.454\t0\t1.224
node:X:child:upos=PRON,node:X:prev:upos=PRON\tNo\t33\t13\tyes\t0.022\t39.394\t39.394\t49.454\t0\t1.224
node:X:child:rel_shallow=nsubj,node:CLH:own:rel_shallow=root,node:X:prev:Definite=Def\tNo\t26\t10\tyes\t0.068\t30.303\t38.462\t37.47\t0\t1.2
node:X:prev:upos=PRON,node:Y:own:has_child=No\tNo\t34\t13\tyes\t0.141\t39.394\t38.235\t48.53\t0\t1.195
node:X:prev:upos=PRON\tNo\t34\t13\tyes\t0.32\t39.394\t38.235\t48.53\t0\t1.195
node:X:child:rel_shallow=nsubj,node:X:own:Mood=Ind,node:X:prev:Number=Sing\tNo\t31\t10\tyes\t0.257\t30.303\t32.258\t33.42\t0\t1.038
node:X:child:Gender=Com,node:X:child:rel_shallow=advmod,node:X:prev:Case=Nom\tNo\t28\t9\tyes\t0.305\t27.273\t32.143\t30.006\t0\t1.035
node:X:child:upos=SCONJ,node:X:own:Mood=Ind,node:X:prev:Number=Sing\tNo\t35\t11\tyes\t0.082\t33.333\t31.429\t36.124\t0\t1.016
node:CLH:own:Voice=Act,node:X:prev:Case=Nom,node:CLH:own:VerbForm=Inf\tNo\t29\t9\tyes\t0.142\t27.273\t31.034\t29.305\t0\t1.005
node:X:child:Gender=Com,node:X:prev:Case=Nom,node:CLH:own:VerbForm=Inf\tNo\t30\t9\tyes\t0.158\t27.273\t30\t28.634\t0\t0.977
node:X:own:Mood=Ind,node:X:prev:Number=Sing,node:X:child:Number=Sing\tNo\t41\t12\tyes\t0.182\t36.364\t29.268\t37.534\t0\t0.957
node:X:own:Mood=Ind,node:X:prev:Number=Sing\tNo\t41\t12\tyes\t0.156\t36.364\t29.268\t37.534\t0\t0.957
node:X:prev:Case=Nom,node:CLH:own:rel_shallow=root\tNo\t48\t14\tyes\t0.245\t42.424\t29.167\t43.684\t0\t0.954
node:X:prev:Case=Nom,node:CLH:own:rel_shallow=root,node:X:child:Case=Nom\tNo\t48\t14\tyes\t0.69\t42.424\t29.167\t43.684\t0\t0.954
node:X:prev:Case=Nom,node:CLH:own:rel_shallow=root,node:Y:own:has_child=No\tNo\t48\t14\tyes\t0.853\t42.424\t29.167\t43.684\t0\t0.954
node:X:own:Tense=Pres,node:CLH:own:rel_shallow=root,node:X:next:upos=PRON\tNo\t25\t6\tyes\t0.327\t18.182\t24\t16.259\t0\t0.806
node:X:child:upos=PRON,node:X:prev:Case=Nom\tNo\t63\t13\tyes\t0.036\t39.394\t20.635\t31.293\t0\t0.705
node:X:child:upos=PRON,node:X:prev:Case=Nom,node:Y:own:has_child=No\tNo\t63\t13\tyes\t0.097\t39.394\t20.635\t31.293\t0\t0.705
node:X:child:upos=ADJ,node:CLH:prev:Definite=Def,node:CLH:own:upos=VERB\tNo\t25\t5\tyes\t0.41\t15.152\t20\t11.731\t0.001\t0.685
node:CLH:own:Voice=Act,node:X:own:Mood=Ind,node:CLH:prev:upos=AUX\tNo\t31\t6\tyes\t0.141\t18.182\t19.355\t13.697\t0\t0.665
node:X:own:Mood=Ind,node:CLH:own:rel_shallow=root,node:X:next:upos=PRON\tNo\t37\t7\tyes\t0.088\t21.212\t18.919\t15.674\t0\t0.651
node:X:prev:Case=Nom,node:Y:own:has_child=No\tNo\t100\t16\tyes\t0.151\t48.485\t16\t30.824\t0\t0.555
node:X:prev:Case=Nom\tNo\t100\t16\tyes\t0.125\t48.485\t16\t30.824\t0\t0.555
node:X:prev:Case=Nom,node:Y:own:has_child=No,node:X:child:Case=Nom\tNo\t100\t16\tyes\t0.224\t48.485\t16\t30.824\t0\t0.555
node:X:prev:Case=Nom,node:X:child:Case=Nom\tNo\t100\t16\tyes\t0.063\t48.485\t16\t30.824\t0\t0.555
node:X:child:upos=ADV,node:CLH:next:upos=SCONJ,sentence:meta:period=1850_1899\tYes\t21\t3\tyes\t0.84\t9.091\t14.286\t5.172\t0.023\t0.496
node:X:own:Tense=Pres,node:X:child:Gender=Neut,node:X:child:Definite=Ind\tNo\t64\t9\tyes\t0.197\t27.273\t14.062\t15.268\t0\t0.488
node:X:own:Tense=Pres,node:CLH:own:Voice=Act,node:CLH:next:upos=SCONJ\tNo\t36\t5\tyes\t0.126\t15.152\t13.889\t8.374\t0.004\t0.482
node:X:own:Tense=Pres,node:X:child:Gender=Neut,node:X:child:Case=Nom\tNo\t76\t10\tyes\t0.123\t30.303\t13.158\t15.818\t0\t0.456
node:X:child:upos=NOUN,node:CLH:next:upos=SCONJ,node:CLH:own:Gender=Neut\tNo\t32\t4\tyes\t0.439\t12.121\t12.5\t5.98\t0.014\t0.432
node:X:own:Tense=Pres,node:X:child:Gender=Neut\tNo\t82\t10\tyes\t0.05\t30.303\t12.195\t14.539\t0\t0.421
node:CLH:own:Voice=Act,node:CLH:own:rel_shallow=root,node:CLH:own:VerbForm=Inf\tNo\t91\t11\tyes\t0.049\t33.333\t12.088\t15.832\t0\t0.417
node:X:child:Gender=Neut,node:X:child:Degree=Pos,node:X:child:Mood=Ind\tNo\t27\t3\tyes\t0.046\t9.091\t11.111\t3.906\t0.048\t0.38
node:X:child:upos=VERB,node:X:child:rel_shallow=advmod,node:X:own:Mood=Ind\tNo\t46\t5\tyes\t0.363\t15.152\t10.87\t6.336\t0.012\t0.371
node:CLH:next:upos=SCONJ,node:CLH:own:Gender=Neut,node:X:own:Voice=Act\tNo\t39\t4\tyes\t0.341\t12.121\t10.256\t4.705\t0.03\t0.347
node:X:child:upos=NOUN,node:CLH:own:Gender=Neut,node:X:own:Voice=Act\tNo\t42\t4\tyes\t0.39\t12.121\t9.524\t5.98\t0.039\t0.318
node:CLH:own:Voice=Act,node:CLH:next:upos=ADV,node:CLH:own:rel_shallow=root\tNo\t43\t4\tyes\t0.436\t12.121\t9.302\t4.113\t0.043\t0.309
node:CLH:next:upos=ADV,node:CLH:own:rel_shallow=root,node:X:own:Voice=Act\tNo\t44\t4\tyes\t0.116\t12.121\t9.091\t3.978\t0.046\t0.301
node:CLH:prev:Voice=Act,node:CLH:own:Voice=Act,node:CLH:prev:upos=AUX\tNo\t100\t9\tyes\t0.091\t27.273\t9\t8.819\t0.003\t0.297
node:CLH:own:Voice=Act,node:CLH:prev:upos=AUX\tNo\t100\t9\tyes\t0.157\t27.273\t9\t8.819\t0.003\t0.297
node:CLH:own:Voice=Act,node:CLH:prev:upos=AUX,node:Y:own:has_child=No\tNo\t100\t9\tyes\t0.034\t27.273\t9\t8.819\t0.003\t0.297
node:CLH:own:Voice=Act,node:CLH:prev:upos=AUX,node:CLH:own:upos=VERB\tNo\t100\t9\tyes\t0.716\t27.273\t9\t8.819\t0.003\t0.297
node:X:child:upos=VERB,node:X:prev:upos=ADV,node:X:child:rel_shallow=mark\tNo\t35\t3\tyes\t0.484\t9.091\t8.571\t2.73\t0.099\t0.279
node:X:own:Tense=Pres,node:X:child:Gender=Com,node:X:child:Definite=Ind\tNo\t139\t11\tyes\t0.088\t33.333\t7.914\t8.791\t0.003\t0.251
node:X:child:Gender=Com,node:X:child:upos=ADV,node:CLH:next:upos=SCONJ\tNo\t82\t6\tyes\t0.116\t18.182\t7.317\t4.173\t0.041\t0.226
node:X:child:Definite=Ind,node:X:child:PronType=Prs,node:X:child:Tense=Past\tNo\t106\t7\tyes\t0.766\t21.212\t6.604\t3.977\t0.046\t0.194
node:X:own:Tense=Pres\tNo\t244\t16\tyes\t0.001\t48.485\t6.557\t8.956\t0.003\t0.192
node:X:own:Tense=Pres,node:X:own:Mood=Ind\tNo\t244\t16\tyes\t0.016\t48.485\t6.557\t8.956\t0.003\t0.192
node:X:own:Tense=Pres,node:Y:own:has_child=No\tNo\t244\t16\tyes\t0\t48.485\t6.557\t8.956\t0.003\t0.192
node:X:own:Tense=Pres,node:X:own:Mood=Ind,node:Y:own:has_child=No\tNo\t244\t16\tyes\t0.147\t48.485\t6.557\t8.956\t0.003\t0.192
node:X:child:upos=ADV,node:X:child:Definite=Ind,sentence:meta:period=1850_1899\tYes\t46\t3\tyes\t0.042\t9.091\t6.522\t1.66\t0.198\t0.19
node:CLH:next:upos=SCONJ,node:X:child:Definite=Ind,node:X:child:Number=Sing\tNo\t207\t13\tyes\t0.006\t39.394\t6.28\t6.621\t0.01\t0.179
node:X:own:Tense=Pres,node:X:own:Voice=Act\tNo\t215\t13\tyes\t0.093\t39.394\t6.047\t6.066\t0.014\t0.168
node:X:own:Tense=Pres,node:X:own:Mood=Ind,node:X:own:Voice=Act\tNo\t215\t13\tyes\t0.123\t39.394\t6.047\t6.066\t0.014\t0.168
node:CLH:own:rel_shallow=root,node:CLH:own:upos=VERB\tNo\t374\t21\tyes\t0.002\t63.636\t5.615\t8.135\t0.004\t0.147
node:CLH:own:rel_shallow=root,node:Y:own:has_child=No,node:CLH:own:upos=VERB\tNo\t374\t21\tyes\t0.197\t63.636\t5.615\t8.135\t0.004\t0.147
node:CLH:own:Voice=Act,node:CLH:next:upos=SCONJ,node:CLH:own:Mood=Ind\tNo\t92\t5\tyes\t1.125\t15.152\t5.435\t1.772\t0.183\t0.139
node:X:child:Gender=Com,node:X:child:rel_shallow=advmod,node:X:child:Definite=Ind\tNo\t208\t11\tyes\t0.249\t33.333\t5.288\t3.604\t0.058\t0.132
node:CLH:own:Voice=Act,node:CLH:next:upos=ADV,node:X:own:Voice=Act\tNo\t95\t5\tyes\t0.069\t15.152\t5.263\t1.615\t0.204\t0.13
node:CLH:own:rel_shallow=root\tNo\t462\t24\tyes\t0.014\t72.727\t5.195\t7.454\t0.006\t0.127
node:CLH:own:rel_shallow=root,node:Y:own:has_child=No\tNo\t462\t24\tyes\t0\t72.727\t5.195\t7.454\t0.006\t0.127
node:X:child:Gender=Com,node:X:own:Mood=Ind,node:X:child:Case=Nom\tNo\t367\t19\tyes\t0.022\t57.576\t5.177\t5.84\t0.016\t0.126
node:CLH:own:rel_shallow=root,node:X:own:Voice=Act,node:CLH:own:upos=VERB\tNo\t335\t17\tyes\t0.233\t51.515\t5.075\t4.911\t0.027\t0.121
node:X:child:Gender=Com,node:X:child:Number=Plur,node:X:own:Voice=Act\tNo\t206\t10\tyes\t0.013\t30.303\t4.854\t2.494\t0.114\t0.11
node:X:child:Gender=Com,node:CLH:own:rel_shallow=root,node:CLH:prev:Case=Nom\tNo\t167\t8\tyes\t0.165\t24.242\t4.79\t1.905\t0.168\t0.107
node:X:child:Number=Plur,node:X:own:Voice=Act,node:X:child:Case=Nom\tNo\t240\t11\tyes\t0.033\t33.333\t4.583\t2.223\t0.136\t0.096
sentence:meta:period=1750_1799,node:X:own:Voice=Act,node:Y:own:has_child=No\tYes\t201\t9\tyes\t0.321\t27.273\t4.478\t1.656\t0.198\t0.091
sentence:meta:period=1750_1799,node:X:own:Voice=Act\tYes\t202\t9\tyes\t0.029\t27.273\t4.455\t1.623\t0.203\t0.09
node:CLH:own:Voice=Act,node:CLH:own:VerbForm=Inf,node:X:own:Voice=Act\tNo\t226\t10\tyes\t0.185\t30.303\t4.425\t1.751\t0.186\t0.088
node:X:child:rel_shallow=obj,sentence:meta:period=1900_1950,node:X:child:Number=Sing\tYes\t116\t5\tyes\t0.256\t15.152\t4.31\t0.781\t0.377\t0.082
node:CLH:prev:Gender=Com,node:X:child:Case=Nom,node:CLH:own:upos=VERB\tNo\t285\t9\tyes\t0.51\t27.273\t3.158\t0.098\t0.755\t0.019
node:X:child:Definite=Ind,node:CLH:own:rel_shallow=conj,node:X:child:Number=Sing\tNo\t159\t5\tyes\t0.215\t15.152\t3.145\t0.05\t0.823\t0.018
node:X:child:rel_shallow=obj,node:X:child:Definite=Def,node:X:child:Voice=Act\tNo\t251\t0\tno\t-0.08\t22.272\t100\t14.488\t0\t0.24
node:X:child:upos=NOUN,node:Y:own:has_child=No,node:X:next:Definite=Ind\tNo\t193\t0\tno\t-0.156\t17.125\t100\t11.14\t0.001\t0.24
node:X:child:rel_shallow=obl,node:X:child:Definite=Ind,node:CLH:prev:Case=Nom\tNo\t135\t0\tno\t-0.202\t11.979\t100\t7.792\t0.005\t0.24
node:Y:own:has_child=No,node:X:next:Voice=Act\tNo\t72\t0\tno\t-0.026\t6.389\t100\t4.156\t0.041\t0.24
node:X:child:upos=NOUN,node:X:next:Gender=Com\tNo\t228\t0\tno\t-0.125\t20.231\t100\t13.161\t0\t0.24
node:X:child:upos=NOUN,node:X:next:Definite=Ind\tNo\t193\t0\tno\t-0.225\t17.125\t100\t11.14\t0.001\t0.24
node:X:child:rel_shallow=mark,node:X:next:Definite=Ind\tNo\t202\t0\tno\t-0.051\t17.924\t100\t11.66\t0.001\t0.24
node:X:child:Gender=Com,node:X:child:rel_shallow=nsubj,node:CLH:own:Definite=Ind\tNo\t145\t0\tno\t-0.262\t12.866\t100\t8.37\t0.004\t0.24
node:X:child:upos=AUX,node:X:own:Voice=Act\tNo\t374\t1\tno\t-0.002\t33.097\t99.733\t14.804\t0\t0.199
node:X:child:upos=AUX,node:X:own:Voice=Act,node:X:child:Voice=Act\tNo\t374\t1\tno\t-0.116\t33.097\t99.733\t14.804\t0\t0.199
node:X:child:Gender=Com,node:X:next:Number=Sing,node:X:child:rel_shallow=obj\tNo\t325\t1\tno\t-0.032\t28.749\t99.692\t12.257\t0\t0.194
node:X:child:upos=NOUN,node:X:next:Number=Sing,node:X:own:Voice=Act\tNo\t302\t1\tno\t-0.003\t26.708\t99.669\t11.076\t0.001\t0.192
node:X:child:VerbForm=Fin,node:X:own:Voice=Act,node:CLH:own:upos=VERB\tNo\t291\t1\tno\t-0.102\t25.732\t99.656\t10.515\t0.001\t0.19
node:X:own:Voice=Act,node:X:child:Mood=Ind,node:CLH:own:upos=VERB\tNo\t290\t1\tno\t-0.109\t25.643\t99.655\t10.465\t0.001\t0.19
node:X:child:upos=NOUN,node:X:next:Number=Sing,node:X:child:Definite=Ind\tNo\t283\t1\tno\t-0.006\t25.022\t99.647\t10.109\t0.001\t0.189
node:X:child:Gender=Com,node:X:child:upos=SCONJ,node:CLH:prev:Case=Nom\tNo\t276\t1\tno\t-0.107\t24.401\t99.638\t9.756\t0.002\t0.188
node:X:child:Gender=Com,node:CLH:prev:Gender=Com,node:X:child:rel_shallow=mark\tNo\t268\t1\tno\t-0.014\t23.691\t99.627\t9.353\t0.002\t0.187
node:X:child:Tense=Pres\tNo\t217\t1\tno\t-0.089\t19.166\t99.539\t6.832\t0.009\t0.177
node:X:next:upos=ADP\tNo\t175\t1\tno\t-0.012\t15.439\t99.429\t4.839\t0.028\t0.166
node:Y:own:has_child=No,node:X:next:upos=ADP\tNo\t175\t1\tno\t-0.024\t15.439\t99.429\t4.839\t0.028\t0.166
node:X:child:rel_shallow=mark,node:X:own:Voice=Act,node:X:child:Voice=Act\tNo\t493\t3\tno\t-0.051\t43.478\t99.391\t13.048\t0\t0.163
node:X:child:rel_shallow=nsubj,node:X:child:Number=Sing,node:CLH:prev:Number=Sing\tNo\t295\t2\tno\t-0.093\t25.998\t99.322\t7.189\t0.007\t0.156
node:X:child:rel_shallow=mark,node:CLH:own:VerbForm=Fin,node:X:own:Voice=Act\tNo\t385\t3\tno\t-0.004\t33.895\t99.221\t8.303\t0.004\t0.147
node:X:child:rel_shallow=nsubj,node:CLH:prev:Number=Sing,node:CLH:prev:Case=Nom\tNo\t247\t2\tno\t-0.184\t21.739\t99.19\t5.132\t0.023\t0.144
node:CLH:prev:Gender=Com,node:X:own:Mood=Ind,node:CLH:prev:Case=Nom\tNo\t115\t1\tno\t-0.502\t10.115\t99.13\t2.218\t0.136\t0.139
node:X:child:upos=AUX\tNo\t426\t4\tno\t-0.135\t37.445\t99.061\t7.528\t0.006\t0.133
node:X:child:upos=AUX,node:X:child:Voice=Act\tNo\t426\t4\tno\t-0.007\t37.445\t99.061\t7.528\t0.006\t0.133
node:X:child:upos=AUX,node:Y:own:has_child=No,node:X:child:Voice=Act\tNo\t425\t4\tno\t-0.039\t37.356\t99.059\t7.49\t0.006\t0.133
node:X:child:upos=AUX,node:Y:own:has_child=No\tNo\t425\t4\tno\t-0.015\t37.356\t99.059\t7.49\t0.006\t0.133
node:X:child:rel_shallow=mark,node:CLH:own:rel_shallow=root,node:CLH:own:VerbForm=Fin\tNo\t201\t2\tno\t-0.09\t17.657\t99.005\t3.305\t0.069\t0.128
node:CLH:own:Voice=Act,node:X:own:Voice=Act,node:X:child:Voice=Act\tNo\t389\t4\tno\t-0.051\t34.161\t98.972\t6.123\t0.013\t0.125
node:X:child:Definite=Def,node:CLH:own:VerbForm=Fin\tNo\t373\t4\tno\t-0.039\t32.742\t98.928\t5.537\t0.019\t0.122
node:X:child:Definite=Def,node:CLH:own:VerbForm=Fin,node:Y:own:has_child=No\tNo\t372\t4\tno\t-0.105\t32.653\t98.925\t5.501\t0.019\t0.122
node:X:child:upos=NOUN,node:X:child:rel_shallow=mark,node:CLH:own:upos=VERB\tNo\t451\t5\tno\t-0.142\t39.574\t98.891\t6.376\t0.012\t0.119
node:X:child:upos=AUX,node:CLH:own:rel_shallow=root\tNo\t175\t2\tno\t-0.053\t15.35\t98.857\t2.361\t0.124\t0.116
node:X:child:upos=AUX,node:CLH:own:rel_shallow=root,node:Y:own:has_child=No\tNo\t175\t2\tno\t-0.035\t15.35\t98.857\t2.361\t0.124\t0.116
node:X:child:upos=AUX,node:CLH:own:rel_shallow=root,node:X:child:Voice=Act\tNo\t175\t2\tno\t-0.089\t15.35\t98.857\t2.361\t0.124\t0.116
node:X:own:Voice=Act,node:X:child:Voice=Act\tNo\t572\t7\tno\t-0.054\t50.133\t98.776\t6.889\t0.009\t0.11
node:X:own:Voice=Act,node:Y:own:has_child=No,node:X:child:Voice=Act\tNo\t571\t7\tno\t-0.081\t50.044\t98.774\t6.856\t0.009\t0.11
node:X:child:upos=ADV,sentence:meta:period=1750_1799,node:CLH:own:upos=VERB\tYes\t74\t1\tno\t-0.055\t6.477\t98.649\t0.738\t0.39\t0.1
node:X:child:rel_shallow=mark,node:X:own:Voice=Act,node:CLH:own:upos=VERB\tNo\t654\t9\tno\t-0.111\t57.232\t98.624\t6.283\t0.012\t0.098
node:X:child:upos=SCONJ,node:X:child:rel_shallow=nsubj,node:X:own:Voice=Act\tNo\t726\t10\tno\t-0.077\t63.531\t98.623\t6.961\t0.008\t0.098
node:X:child:Gender=Com,node:X:child:rel_shallow=mark,node:CLH:own:upos=VERB\tNo\t604\t9\tno\t-0.012\t52.795\t98.51\t4.839\t0.028\t0.09
node:X:child:rel_shallow=mark,node:X:own:Voice=Act\tNo\t892\t14\tno\t-0.078\t77.906\t98.43\t6.248\t0.012\t0.084
node:X:child:rel_shallow=mark,node:X:own:Voice=Act,node:Y:own:has_child=No\tNo\t891\t14\tno\t-0.236\t77.817\t98.429\t6.222\t0.013\t0.084
node:X:child:Definite=Def,node:X:child:Number=Sing,node:X:own:Voice=Act\tNo\t745\t12\tno\t-0.001\t65.04\t98.389\t4.853\t0.028\t0.081
node:X:child:rel_shallow=mark,node:X:child:Case=Nom,node:CLH:own:upos=VERB\tNo\t674\t11\tno\t-0.087\t58.829\t98.368\t4.225\t0.04\t0.079
node:X:child:rel_shallow=nsubj,node:X:child:Definite=Def,node:X:child:Number=Sing\tNo\t708\t12\tno\t-0.122\t61.757\t98.305\t3.95\t0.047\t0.075
node:X:child:rel_shallow=nsubj,node:X:child:Number=Sing,node:X:own:Voice=Act\tNo\t802\t14\tno\t-0.116\t69.92\t98.254\t4.056\t0.044\t0.071
node:X:child:rel_shallow=nsubj,node:X:child:Definite=Def,node:X:own:Voice=Act\tNo\t735\t13\tno\t-0.056\t64.064\t98.231\t3.55\t0.06\t0.069
node:X:child:Voice=Act\tNo\t647\t12\tno\t-0.185\t56.344\t98.145\t2.611\t0.106\t0.064
node:Y:own:has_child=No,node:X:child:Voice=Act\tNo\t646\t12\tno\t-0.012\t56.256\t98.142\t2.59\t0.108\t0.063
node:X:child:rel_shallow=mark\tNo\t996\t19\tno\t-0.174\t86.69\t98.092\t3.572\t0.059\t0.06
node:X:child:rel_shallow=mark,node:Y:own:has_child=No\tNo\t995\t19\tno\t-0.208\t86.602\t98.09\t3.553\t0.059\t0.06
node:X:child:rel_shallow=nsubj,node:X:own:Voice=Act,node:Y:own:has_child=No\tNo\t869\t17\tno\t-0.197\t75.599\t98.044\t2.782\t0.095\t0.057
node:X:child:upos=ADV,node:X:own:Voice=Act,node:CLH:own:upos=VERB\tNo\t301\t6\tno\t-0.431\t26.176\t98.007\t0.88\t0.348\t0.054
node:X:child:Definite=Def,node:X:child:Number=Sing,node:CLH:own:upos=VERB\tNo\t613\t13\tno\t-0.08\t53.239\t97.879\t1.273\t0.259\t0.046
node:X:child:upos=PRON,node:X:child:Definite=Def,node:X:child:Number=Sing\tNo\t703\t15\tno\t-0.003\t61.047\t97.866\t1.406\t0.236\t0.045
node:X:child:Gender=Com,node:X:own:Voice=Act,node:X:child:Case=Nom\tNo\t849\t22\tno\t0.163\t73.381\t97.409\t0.203\t0.652\t0.015
node:X:child:upos=NOUN,node:X:child:rel_shallow=nsubj,node:CLH:own:rel_shallow=root\tNo\t224\t6\tno\t-0.166\t19.343\t97.321\t0.023\t0.88\t0.01
node:X:child:rel_shallow=nsubj,node:CLH:own:rel_shallow=root,sentence:meta:period=1750_1799\tYes\t73\t2\tno\t-0.453\t6.3\t97.26\t0.003\t0.957\t0.006
"""

# ── main ──────────────────────────────────────────────────────────────────────

def load_data(filepath=None):
    if filepath:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
            look_up_pattern = 'Pattern,Period Predictor,p_occs,p_q_occs,Decision,Coef,Coverage,Precision,G-statistic,p-value,Cramers_phi'
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.strip() == look_up_pattern:
                    lines_before_content = i
                    break
            real_content = "\n".join(lines[lines_before_content:])
            # print(f"Header found at line {i+1}, {real_content}.")
                    
                    
            reader = csv.DictReader(StringIO(real_content.strip()), delimiter=",")
    else:
        content = EMBEDDED_DATA
        reader = csv.DictReader(StringIO(content.strip()), delimiter="\t")
    
    return list(reader)

def process(rows, alpha=0.05, min_q=5):
    #print("ROWS in process:", rows)
    n_tests = len(rows)
    bonf_threshold = alpha / n_tests

    results = []
    for r in rows:
        try:
            p_occs   = int(r["p_occs"])
            p_q_occs = int(r["p_q_occs"])
            phi      = float(r["Cramers_phi"])
            pval     = float(r["p-value"])
            prec     = float(r["Precision"])
            pattern  = r["Pattern"]
            period_pred = r.get("Period Predictor", "No")
            decision = str(r["Decision"]).strip().lower()
        except (ValueError, KeyError):
            print(f"Skipping row with invalid data: {r}")
            continue

        bonf_sig   = pval < bonf_threshold
        raw_sig    = pval < alpha
        eff        = phi_label(phi)
        vert       = verdict(pval, bonf_threshold, phi, p_q_occs, min_q)
        dirn       = direction(period_pred, prec)

        results.append({
            "Pattern":           pattern,
            "Period_pred":       period_pred,
            "p_occs":            p_occs,
            "p_q_occs":          p_q_occs,
            "Precision_%":       f"{prec:.1f}",
            "phi":               f"{phi:.3f}",
            "Effect_size":       eff,
            "p_raw":             f"{pval:.4f}" if pval >= 0.0001 else "< .0001",
            "p_bonf_threshold":  f"{bonf_threshold:.6f}",
            "Bonf_sig":          "YES" if bonf_sig else "no",
            "Raw_sig_only":      "YES" if (raw_sig and not bonf_sig) else "",
            "Decision":          decision,
            "Verdict":           vert,
            "_pval":             pval,   # for sorting
            "_phi":              phi,
        })
    #print(f"Number of results: {len(results)}")
    results.sort(key=lambda x: (-abs(x["_phi"]), x["_pval"]))
    return results, bonf_threshold, n_tests

def write_csv(rows, path):
    if not rows:
        return
    keys = [k for k in rows[0] if not k.startswith("_")]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in keys})

def print_summary(results, bonf_threshold, n_tests, alpha):
    total     = len(results)
    bonf_sig  = [r for r in results if r["Bonf_sig"] == "YES"]
    raw_only  = [r for r in results if r["Raw_sig_only"] == "YES"]
    low_n     = [r for r in results if r["Verdict"] == "LOW N"]
    strong    = [r for r in results if r["Verdict"] == "STRONG"]
    moderate  = [r for r in results if r["Verdict"] == "MODERATE"]

    sep = "─" * 72
    print(sep)
    print(f"  BONFERRONI CORRECTION SUMMARY")
    print(f"  Total patterns tested : {n_tests}")
    print(f"  Family-wise alpha     : {alpha}")
    print(f"  Bonferroni threshold  : {alpha}/{n_tests} = {bonf_threshold:.6f}")
    print(sep)
    print(f"  Significant after Bonferroni : {len(bonf_sig)}")
    print(f"    ↳ STRONG effect (φ ≥ 0.5)  : {len(strong)}")
    print(f"    ↳ MODERATE effect (φ ≥ 0.3): {len(moderate)}")
    print(f"  Significant raw only (p<.05) : {len(raw_only)}  ← likely false positives")
    print(f"  Low co-occurrence N (<min_q) : {len(low_n)}")
    print(sep)

    if bonf_sig:
        print(f"\n  PATTERNS SURVIVING BONFERRONI CORRECTION  (sorted by |φ|)\n")
        hdr = f"  {'φ':>6}  {'Effect':10}  {'p_raw':>8}  {'p_q':>5}  {'Prec%':>6}  Pattern"
        print(hdr)
        print("  " + "·" * 68)
        for r in bonf_sig:
            print(f"  {r['phi']:>6}  {r['Effect_size']:10}  {r['p_raw']:>8}  "
                  f"{r['p_q_occs']:>5}  {r['Precision_%']:>6}  {r['Pattern'][:55]}")
    else:
        print("\n  No patterns survive Bonferroni correction.")

    if raw_only:
        print(f"\n  PATTERNS SIGNIFICANT ONLY WITHOUT CORRECTION  (likely false positives)\n")
        hdr = f"  {'φ':>6}  {'p_raw':>8}  {'p_q':>5}  Pattern"
        print(hdr)
        print("  " + "·" * 60)
        for r in raw_only:
            print(f"  {r['phi']:>6}  {r['p_raw']:>8}  {r['p_q_occs']:>5}  {r['Pattern'][:55]}")

    print(f"\n{sep}")
    print(f"  Output files written:")
    print(f"    bonferroni_all_patterns.csv      — full table with all columns")
    print(f"    bonferroni_significant.csv       — Bonferroni-significant only")
    print(f"    bonferroni_raw_sig_only.csv      — raw-sig but not Bonferroni (caution)")
    print(sep)

def main():
    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to pattern results.")
    parser.add_argument("--input",  default=None,  help="Path to TSV input file (uses embedded data if omitted)")
    parser.add_argument("--alpha",  default=0.05,  type=float, help="Family-wise alpha (default 0.05)")
    parser.add_argument("--min-q",  default=5,     type=int,   help="Minimum co-occurrences to report (default 5)")
    args = parser.parse_args()

    rows = load_data(args.input)
    print(f"Loaded {len(rows)} rows from {'embedded data' if args.input is None else args.input}")
    results, bonf_threshold, n_tests = process(rows, alpha=args.alpha, min_q=args.min_q)
    #print(len(results))

    # Write all three files
    write_csv(results, "bonferroni_all_patterns.csv")
    write_csv([r for r in results if r["Bonf_sig"] == "YES"],
              "bonferroni_significant.csv")
    write_csv([r for r in results if r["Raw_sig_only"] == "YES"],
              "bonferroni_raw_sig_only.csv")

    print_summary(results, bonf_threshold, n_tests, args.alpha)

# fix the write_csv calls above (overloaded signature by mistake)
def write_csv(rows, path):
    if not rows:
        with open(path, "w", encoding="utf-8") as f:
            f.write("(no rows matched this filter)\n")
        return
    keys = [k for k in rows[0] if not k.startswith("_")]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in keys})

if __name__ == "__main__":
    main()
