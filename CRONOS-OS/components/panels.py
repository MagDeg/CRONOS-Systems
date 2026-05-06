from dash import html, dcc


def Panel(index, content, widget, link=None, variant=None, config=None):
    classes = ["panel"]
    if variant:
        classes.append(f"panel-{variant}")

    href = link or f"/panel/{index}"
    inner = dcc.Link(
        content,
        href=str(href),
        style={
            "color": "inherit",
            "textDecoration": "none",
            "width": "100%",
            "height": "100%"
        },
    )
    store = dcc.Store(
        id={'type': 'panel-config', 'index': index},
        data={**(config or {}), "widget": widget, "index": index}
    )


    return html.Div([store, inner], className=" ".join(classes))

