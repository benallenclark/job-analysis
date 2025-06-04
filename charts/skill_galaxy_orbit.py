from pythreejs import (
    BufferGeometry,
    BufferAttribute,
    Points,
    PointsMaterial,
    Scene,
    PerspectiveCamera,
    Renderer,
    AmbientLight,
    DirectionalLight,
    OrbitControls
)
from IPython.display import display, HTML, Javascript
import numpy as np
import networkx as nx
import uuid
import json

def launch_skill_galaxy_orbit(job_skill_map, max_skills=2000, min_edge_weight=0):
    # Step 1: Co-occurrence graph
    co_occurrence = {}
    for skills in job_skill_map.values():
        skills = list(skills)
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                a, b = skills[i].lower(), skills[j].lower()
                edge = tuple(sorted([a, b]))
                co_occurrence[edge] = co_occurrence.get(edge, 0) + 1

    G = nx.Graph()
    for (a, b), weight in co_occurrence.items():
        if weight >= min_edge_weight:
            G.add_edge(a, b, weight=weight)

    if not G:
        print("⚠️ Not enough edges to build a galaxy graph.")
        return

    # Step 2: Limit nodes by degree
    if len(G.nodes) > max_skills:
        top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:max_skills]
        G = G.subgraph([n for n, _ in top_nodes]).copy()

    # Step 3: Layout
    pos = nx.spring_layout(G, dim=3, weight="weight", seed=42)
    labels = list(G.nodes())
    coords = np.array([pos[n] for n in labels])
    coords -= coords.mean(axis=0)
    coords /= coords.std()
    coords[:, 2] *= 2.5  # boost z-depth

    # Step 4: Color nodes by degree
    degrees = dict(G.degree)
    max_deg = max(degrees.values()) or 1
    colors = np.array([
        [(degrees[n] / max_deg), 0.3, (1 - degrees[n] / max_deg)]
        for n in labels
    ])

    geometry = BufferGeometry(attributes={
        'position': BufferAttribute(coords.astype(np.float32)),
        'color': BufferAttribute(colors.astype(np.float32))
    })

    material = PointsMaterial(
        size=0.08,
        vertexColors='VertexColors',
        sizeAttenuation=True,
        transparent=True,
        opacity=0.7
    )
    points = Points(geometry=geometry, material=material)

    # Scene with dark background
    scene = Scene(
        children=[
            points,
            AmbientLight(intensity=0.6),
            DirectionalLight(position=[3, 5, 1], intensity=0.5)
        ],
        background='#111111'
    )

    # Camera and controls
    camera = PerspectiveCamera(position=[0, 0, 4], fov=70)
    controls = OrbitControls(controlling=camera)

    # Unique ID
    container_id = "skillgalaxy-" + str(uuid.uuid4())
    labels_json = json.dumps(labels)
    coords_2d = coords[:, :2].tolist()


    renderer = Renderer(
        camera=camera,
        scene=scene,
        controls=[controls],
        width=900,
        height=700,
        antialias=True,
        alpha=False,
        container_id=container_id
    )

    display(renderer)
    display(HTML(f"""
    <script type="module">
    (async function () {{
        // Wait for the canvas and THREE to load
        const tryGetCanvas = () => document.querySelector("#{container_id} canvas");
        while (!window.THREE || !tryGetCanvas()) await new Promise(r => setTimeout(r, 200));

        const labels = {json.dumps(labels)};
        const tooltip = document.createElement('div');
        Object.assign(tooltip.style, {{
            position: 'fixed',
            background: 'rgba(0,0,0,0.8)',
            color: '#fff',
            padding: '4px 8px',
            borderRadius: '5px',
            fontFamily: 'monospace',
            fontSize: '12px',
            pointerEvents: 'none',
            display: 'none',
            zIndex: 10000
        }});
        document.body.appendChild(tooltip);

        const canvas = tryGetCanvas();
        const rendererEl = Object.values(window).find(v => v?.domElement === canvas);
        const camera = rendererEl?.camera;
        const scene = rendererEl?.scene;
        const points = scene.children.find(c => c.isPoints);

        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();

        canvas.addEventListener('mousemove', e => {{
            const rect = canvas.getBoundingClientRect();
            mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObject(points);

            if (intersects.length > 0) {{
                const index = intersects[0].index;
                tooltip.textContent = labels[index];
                tooltip.style.left = (e.clientX + 10) + 'px';
                tooltip.style.top = (e.clientY + 10) + 'px';
                tooltip.style.display = 'block';
            }} else {{
                tooltip.style.display = 'none';
            }}
        }});
    }})();
    </script>
    """))
