"""
Dashboard app for Global AI Knowledge Engine
Interactive Streamlit visualization.
"""

import streamlit as st
import json
import time
from pathlib import Path
from collections import Counter

st.set_page_config(
    page_title="Global AI Knowledge Engine",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_graph_data(graph_path: str = "data/knowledge_graph.json") -> dict:
    """Load graph data from JSON for visualization."""
    path = Path(graph_path)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {"nodes": [], "edges": [], "metadata": {}}


def render_graph_html(nodes, edges):
    """Render an interactive graph visualization."""
    import json as json_lib
    nodes_json = json_lib.dumps(nodes[:200])
    edges_json = json_lib.dumps(edges[:500])
    html = (
        "<html><head>"
        '<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>'
        "<style>#g{width:100%;height:600px;border:1px solid #444;background:#0e1117}</style>"
        "</head><body><div id=\"g\"></div><script>"
        "const nodes=new vis.DataSet(" + nodes_json + ");"
        "const edges=new vis.DataSet(" + edges_json + ");"
        "const opts={nodes:{shape:\"dot\",scaling:{min:5,max:30},font:{color:\"#fff\",size:12},"
        "color:{background:\"#4CAF50\",border:\"#2196F3\"}},"
        "edges:{arrows:{to:{enabled:true,scaleFactor:0.5}},color:{color:\"#555\"}},"
        "physics:{stabilization:false}};"
        "new vis.Network(document.getElementById(\"g\"),{nodes,edges},opts);"
        "</script></body></html>"
    )
    st.components.v1.html(html, height=620)


def main():
    st.title("🌍 Global AI Knowledge Engine")
    st.caption("Building structured knowledge about the world — continuously")
    st.divider()

    with st.sidebar:
        st.header("⚙️ Controls")
        graph_path = st.text_input("Graph path", value="data/knowledge_graph.json")
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
        st.divider()
        st.header("🔍 Entity Search")
        search_query = st.text_input("Search entities...", placeholder="e.g. OpenAI, climate")
        entity_type_filter = st.selectbox("Entity type", [
            "All", "person", "organization", "location", "event", "product", "group"
        ])
        st.divider()
        view_mode = st.radio("View", [
            "Graph Stats", "Entity Explorer", "Graph Visualization", "Live Feed"
        ])

    graph_data = load_graph_data(graph_path)
    metadata = graph_data.get("metadata", {})
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if view_mode == "Graph Stats":
        st.header("📈 Knowledge Graph Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔵 Total Nodes", f"{len(nodes):,}")
        with col2:
            st.metric("🔗 Total Edges", f"{len(edges):,}")
        with col3:
            st.metric("🔄 Update Cycles", metadata.get("update_count", 0))
        with col4:
            last_saved = metadata.get("saved_at", "Never")
            st.metric("⏰ Last Updated", last_saved[:16] if last_saved != "Never" else "Never")
        st.divider()
        if nodes:
            type_counts = Counter(n.get("label", "unknown") for n in nodes)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Entity Types Distribution")
                import pandas as pd
                df = pd.DataFrame(
                    [(k, v) for k, v in type_counts.most_common()],
                    columns=["Type", "Count"]
                )
                st.bar_chart(df.set_index("Type"))
            with col2:
                st.subheader("Top 15 Most Mentioned")
                top_nodes = sorted(nodes, key=lambda x: x.get("mentions", 1), reverse=True)[:15]
                for node in top_nodes:
                    mentions = node.get("mentions", 1)
                    label = node.get("label", "unknown")
                    text = node.get("text", node.get("id", ""))
                    st.write(f"**{text}** `{label}` — {mentions} mentions")

    elif view_mode == "Entity Explorer":
        st.header("🔍 Entity Explorer")
        if search_query:
            query_lower = search_query.lower()
            et_filter = None if entity_type_filter == "All" else entity_type_filter
            filtered = [
                n for n in nodes
                if query_lower in n.get("text", "").lower()
            ]
            if et_filter:
                filtered = [n for n in filtered if n.get("label") == et_filter]
            st.write(f"Found **{len(filtered)}** entities matching '{search_query}'")
            for node in filtered[:20]:
                with st.expander(f"**{node.get('text', node['id'])}** — `{node.get('label', 'unknown')}`"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID:** {node['id']}")
                        st.write(f"**Type:** {node.get('label', 'unknown')}")
                        st.write(f"**Mentions:** {node.get('mentions', 1)}")
                    with col2:
                        sources = node.get("sources", [])
                        st.write(f"**Sources:** {len(sources)}")
        else:
            st.info("Enter a search query in the sidebar")
            st.subheader("Top 30 Most Connected Entities")
            top_nodes = sorted(nodes, key=lambda x: x.get("mentions", 1), reverse=True)[:30]
            if top_nodes:
                import pandas as pd
                df = pd.DataFrame(top_nodes)
                if "text" in df and "label" in df and "mentions" in df:
                    st.dataframe(df[["text", "label", "mentions"]], use_container_width=True)

    elif view_mode == "Graph Visualization":
        st.header("🕸️ Interactive Knowledge Graph")
        if not nodes:
            st.warning("No graph data. Run the pipeline to build the graph.")
        else:
            label_colors = {
                "person": "#FF6384", "organization": "#36A2EB", "location": "#FFCE56",
                "event": "#4BC0C0", "product": "#9966FF", "unknown": "#C9CBCF"
            }
            vis_nodes = [
                {
                    "id": n["id"],
                    "label": n.get("text", n["id"])[:30],
                    "group": n.get("label", "unknown"),
                    "value": n.get("mentions", 1),
                    "color": label_colors.get(n.get("label", "unknown"), "#C9CBCF")
                }
                for n in nodes[:300]
            ]
            vis_edges = [
                {"from": e["source"], "to": e["target"],
                 "label": e.get("predicate", ""), "arrows": "to"}
                for e in edges[:500]
            ]
            render_graph_html(vis_nodes, vis_edges)
            st.caption(f"Showing {len(vis_nodes)} nodes, {len(vis_edges)} edges")

    elif view_mode == "Live Feed":
        st.header("📡 Live Knowledge Update Feed")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nodes", len(nodes))
        with col2:
            st.metric("Edges", len(edges))
        with col3:
            st.metric("Last Update", metadata.get("saved_at", "Never")[:16])
        st.subheader("Recent Sources")
        all_sources = []
        for node in nodes:
            all_sources.extend(node.get("sources", []))
        unique_sources = list(set(all_sources))[-20:]
        for src in unique_sources:
            if src:
                st.write(f"📰 {src[:80]}")
        if auto_refresh:
            time.sleep(30)
            st.rerun()


def start_dashboard():
    """Entry point for starting the dashboard."""
    import subprocess
    subprocess.run(["streamlit", "run", __file__])


if __name__ == "__main__":
    main()
