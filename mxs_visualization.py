"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import mxs_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_kernmatrix(kerne, titel: str):
    """Klausel-Matrix: je Zeile eine Annahme (weiche Klausel, Relaxation oder Zähler), je Spalte ein Kern; ein gefülltes Feld heißt „die Annahme gehört zum Kern“.
    `kerne`: Liste von `KernSchritt`. Die Zeilen stehen in der Reihenfolge ihres ersten Auftretens."""
    zeilen = []
    for k in kerne:
        for m in k.mitglieder:
            if m not in zeilen:
                zeilen.append(m)
    z = [[1 if m in k.mitglieder else 0 for k in kerne] for m in zeilen]
    text = [["●" if v else "" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(z=z, x=[f"Kern {k.nr}" for k in kerne], y=zeilen, text=text, texttemplate="%{text}", showscale=False,
                               colorscale=[[0, "rgba(128,128,128,0.08)"], [1, C.COLOR_KERN]], xgap=3, ygap=3, hoverinfo="skip"))
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(type="category", side="top")
    fig.update_layout(title=dict(text=titel, font=dict(size=14), y=0.02, yanchor="bottom"))
    return _base(fig, height=max(200, 34 * len(zeilen) + 90))


def build_zeitleiste(laeufe: dict, titel: str):
    """Untere Schranke (durchgezogen) und obere Schranke (gestrichelt, soweit bekannt) nach jedem SAT-Aufruf; `laeufe`: Verfahren -> `Lauf`."""
    fig = go.Figure()
    for v, lauf in laeufe.items():
        zl = lauf.zeitleiste
        if not zl:
            continue
        xs = list(range(1, len(zl) + 1))
        fig.add_trace(go.Scatter(x=xs, y=[e["untere"] for e in zl], mode="lines+markers", line=dict(color=C.COLOR[v], width=2, shape="hv"), name=C.VERFAHREN_LABEL[v],
                                 customdata=[[e["antwort"], e["konflikte"]] for e in zl],
                                 hovertemplate="Aufruf %{x} (%{customdata[0]}): untere Schranke %{y}, %{customdata[1]} Konflikte<extra>" + C.VERFAHREN_LABEL[v] + "</extra>"))
        obere = [(x, e["obere"]) for x, e in zip(xs, zl) if e["obere"] is not None]
        if obere:
            fig.add_trace(go.Scatter(x=[p[0] for p in obere], y=[p[1] for p in obere], mode="lines+markers", line=dict(color=C.COLOR[v], width=1, dash="dot", shape="hv"),
                                     marker=dict(symbol="x"), showlegend=False, hovertemplate="Aufruf %{x}: obere Schranke %{y}<extra>" + C.VERFAHREN_LABEL[v] + "</extra>"))
    fig.update_xaxes(title_text="SAT-Aufruf", dtick=1 if max((len(l.zeitleiste) for l in laeufe.values()), default=0) <= 15 else None)
    fig.update_yaxes(title_text="Schranke auf die Kosten (durchgezogen unten, gepunktet oben)")
    fig.update_layout(title=dict(text=titel, font=dict(size=14)))
    return _base(fig)


def build_streifen(konflikte: dict, budget: int, titel: str):
    """Konflikte je Instanz (ein Punkt je Instanz) und Verfahren; die Raute ist der Median. Logarithmische Achse; Abbrüche liegen auf dem Budget."""
    fig = go.Figure()
    sichtbar = [(v, w) for v, w in konflikte.items() if w]
    for pos, (v, werte) in enumerate(sichtbar):
        label = C.VERFAHREN_LABEL.get(v, C.CPSAT_LABEL)
        n = len(werte)
        xs = [pos + (i / max(n - 1, 1) - 0.5) * 0.5 for i in range(n)]
        fig.add_trace(go.Scatter(x=xs, y=[max(w, 0.5) for w in werte], mode="markers", marker=dict(color=C.COLOR[v], size=9, opacity=0.65), name=label,
                                 customdata=[[i + 1, w] for i, w in enumerate(werte)],
                                 hovertemplate="Instanz %{customdata[0]}: %{customdata[1]:,} Konflikte<extra>" + label + "</extra>"))
        ordnung = sorted(werte)
        med = ordnung[n // 2] if n % 2 else (ordnung[n // 2 - 1] + ordnung[n // 2]) / 2
        fig.add_trace(go.Scatter(x=[pos], y=[max(med, 0.5)], mode="markers", marker=dict(color="rgba(0,0,0,0)", size=17, symbol="diamond-open", line=dict(color=C.COLOR[v], width=3)),
                                 showlegend=False, hovertemplate=f"Median {med:,.1f}<extra>{label}</extra>"))
    fig.update_xaxes(tickvals=list(range(len(sichtbar))), ticktext=[C.VERFAHREN_LABEL.get(v, "CP-SAT") for v, _ in sichtbar], range=[-0.6, max(len(sichtbar) - 1, 0) + 0.6])
    fig.update_yaxes(title_text="Konflikte je Instanz (logarithmisch; Raute = Median)", type="log")
    fig.update_layout(title=dict(text=titel, font=dict(size=14)), showlegend=False)
    if any(max(w) >= budget for _, w in sichtbar):
        fig.add_hline(y=budget, line_dash="dot", line_color="rgba(150,150,150,0.8)", annotation_text="Budget", annotation_position="top left")
    return _base(fig)


def build_klauseln(werte: dict, titel: str):
    """Balken der Klauselzahlen (logarithmisch): `werte` = {Beschriftung: Klauseln}."""
    fig = go.Figure(go.Bar(x=list(werte), y=list(werte.values()), marker=dict(color=[C.COLOR["lin_unten"] if "unär" in k or "Gewicht" in k else C.COLOR["oll"] for k in werte]),
                           text=[f"{v:,}".replace(",", ".") for v in werte.values()], textposition="outside", hovertemplate="%{x}: %{y:,} Klauseln<extra></extra>"))
    fig.update_yaxes(title_text="Klauseln (logarithmisch)", type="log")
    fig.update_layout(title=dict(text=titel, font=dict(size=14)), showlegend=False)
    return _base(fig)


def build_minimierung(paare: list, titel: str):
    """Je Zelle zwei Balken: Gesamtkonflikte (Median) ohne und mit Kernminimierung. `paare`: Liste von (Zellenname, ohne, mit)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name="ohne Minimierung", x=[p[0] for p in paare], y=[max(p[1], 0.5) for p in paare], marker_color=C.COLOR["oll"]))
    fig.add_trace(go.Bar(name="mit Minimierung", x=[p[0] for p in paare], y=[max(p[2], 0.5) for p in paare], marker_color=C.COLOR["oll_min"]))
    fig.update_yaxes(title_text="Konflikte, Median (logarithmisch)", type="log")
    fig.update_layout(title=dict(text=titel, font=dict(size=14)), barmode="group")
    return _base(fig)
