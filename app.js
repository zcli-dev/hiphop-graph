const relatedForm = document.getElementById("related-form");
const pathForm = document.getElementById("path-form");
const inputOne = document.getElementById("artist-one");
const inputA = document.getElementById("path-a");
const inputB = document.getElementById("path-b");
const nameList = document.getElementById("artist-names");
const result = document.getElementById("result");
const chain = document.getElementById("chain");
const lists = document.getElementById("lists");
const legend = document.getElementById("legend");
const directList = document.getElementById("direct-list");
const similarList = document.getElementById("similar-list");

const TOP = 10;

function simplify(text) {
  return text.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
}

function songCount(songs) {
  return `${songs} ${songs === 1 ? "song" : "songs"}`;
}

function describeStep(step) {
  if (step.type === "credited together") {
    return `credited on ${songCount(step.songs)} together`;
  }
  const base = step.type === "member of band" ? "connected through a group" : step.type;
  return step.songs > 0 ? `${base}, and credited on ${songCount(step.songs)} together` : base;
}

function shortLabel(step) {
  if (step.type === "credited together") return songCount(step.songs);
  const base = step.type === "member of band" ? "same group" : step.type;
  return step.songs > 0 ? `${base}, ${songCount(step.songs)}` : base;
}

fetch("graph.json")
  .then((response) => response.json())
  .then(start)
  .catch((error) => {
    console.error(error);
    result.textContent = "Something went wrong loading the data.";
  });

function start(data) {
  const neighbors = new Map();
  const nameById = new Map();
  const degreeById = new Map();
  const idByName = new Map();

  data.nodes.forEach((node) => {
    neighbors.set(node.id, []);
    nameById.set(node.id, node.name);
    degreeById.set(node.id, node.degree);
  });

  data.nodes.forEach((node) => {
    const key = simplify(node.name);
    const existing = idByName.get(key);
    if (existing === undefined || node.degree > degreeById.get(existing)) {
      idByName.set(key, node.id);
    }
  });

  data.edges.forEach((edge) => {
    neighbors.get(edge.source).push({ id: edge.target, type: edge.type, songs: edge.songs });
    neighbors.get(edge.target).push({ id: edge.source, type: edge.type, songs: edge.songs });
  });

  [...data.nodes]
    .sort((a, b) => b.degree - a.degree)
    .forEach((node) => {
      const option = document.createElement("option");
      option.value = node.name;
      nameList.appendChild(option);
    });

  const cy = cytoscape({
    container: document.getElementById("graph"),
    elements: [],
    style: [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "font-size": 11,
          color: "#e8eaf2",
          "text-valign": "bottom",
          "text-margin-y": 4,
          "text-outline-width": 2,
          "text-outline-color": "#181c2e",
          width: 16,
          height: 16,
          "background-color": "#6b7a99",
        },
      },
      {
        selector: 'node[kind = "center"]',
        style: { width: 30, height: 30, "background-color": "#ffb703", "font-size": 13, "font-weight": "bold" },
      },
      { selector: 'node[kind = "direct"]', style: { "background-color": "#4cc9f0" } },
      { selector: 'node[kind = "similar"]', style: { "background-color": "#80ed99" } },
      { selector: 'node[kind = "path"]', style: { width: 22, height: 22, "background-color": "#ffb703" } },
      {
        selector: "edge",
        style: { width: "mapData(songs, 0, 30, 1, 5)", "line-color": "#3a4256" },
      },
      {
        selector: "edge[label]",
        style: {
          label: "data(label)",
          "font-size": 10,
          color: "#9aa3bd",
          "text-rotation": "autorotate",
          "text-background-color": "#181c2e",
          "text-background-opacity": 1,
          "text-background-padding": 2,
          "line-color": "#ffb703",
          width: 3,
        },
      },
    ],
  });

  function draw(elements, layout) {
    cy.elements().remove();
    cy.add(elements);
    cy.layout(layout).run();
    cy.fit(undefined, 40);
  }

  function edgesAmong(ids) {
    const inSet = new Set(ids);
    const found = [];
    ids.forEach((id) => {
      neighbors.get(id).forEach((other) => {
        if (inSet.has(other.id) && id < other.id) {
          found.push({ data: { id: id + "|" + other.id, source: id, target: other.id, songs: other.songs } });
        }
      });
    });
    return found;
  }

  function related(id) {
    const first = neighbors.get(id);
    const direct = new Set(first.map((n) => n.id));
    const scores = new Map();

    first.forEach((n) => {
      const weight = 1 / Math.log(neighbors.get(n.id).length + 1);
      neighbors.get(n.id).forEach((m) => {
        if (m.id === id) return;
        const entry = scores.get(m.id) || { score: 0, via: [] };
        entry.score += weight;
        entry.via.push(n.id);
        scores.set(m.id, entry);
      });
    });

    const similar = [...scores.entries()]
      .filter(([otherId]) => !direct.has(otherId))
      .sort((a, b) => b[1].score - a[1].score)
      .slice(0, TOP)
      .map(([otherId, entry]) => ({ id: otherId, via: entry.via }));

    const worked = [...first]
      .sort((a, b) => b.songs - a.songs || neighbors.get(b.id).length - neighbors.get(a.id).length)
      .slice(0, TOP);

    return { worked, similar };
  }

  function nameButton(id) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "link";
    button.textContent = nameById.get(id);
    button.addEventListener("click", () => showRelated(id));
    return button;
  }

  function fillList(list, items) {
    list.replaceChildren();
    items.forEach((item) => {
      const li = document.createElement("li");
      const detail = document.createElement("span");
      detail.textContent = " " + item.text;
      li.append(nameButton(item.id), detail);
      list.appendChild(li);
    });
  }

  function showRelated(id) {
    const { worked, similar } = related(id);
    inputOne.value = nameById.get(id);

    fillList(
      directList,
      worked.map((n) => ({ id: n.id, text: describeStep(n) }))
    );
    fillList(
      similarList,
      similar.map((s) => {
        const names = s.via.slice(0, 3).map((v) => nameById.get(v));
        const more = s.via.length - names.length;
        return { id: s.id, text: `both worked with ${names.join(", ")}${more > 0 ? ` and ${more} more` : ""}` };
      })
    );

    const kind = new Map([[id, "center"]]);
    worked.forEach((n) => kind.set(n.id, "direct"));
    similar.forEach((s) => {
      if (!kind.has(s.id)) kind.set(s.id, "similar");
    });
    const ids = [...kind.keys()];

    draw(
      [
        ...ids.map((x) => ({ data: { id: x, label: nameById.get(x), kind: kind.get(x) } })),
        ...edgesAmong(ids),
      ],
      { name: "cose", animate: false, numIter: 400, nodeRepulsion: 9000, idealEdgeLength: 70 }
    );

    chain.hidden = true;
    lists.hidden = false;
    legend.hidden = false;
    result.textContent = `${nameById.get(id)} has ${neighbors.get(id).length} connections in the data. Click any name or dot to explore from there.`;
  }

  function findPath(startId, endId) {
    const previous = new Map([[startId, null]]);
    const queue = [startId];
    while (queue.length > 0) {
      const current = queue.shift();
      if (current === endId) break;
      for (const next of neighbors.get(current)) {
        if (!previous.has(next.id)) {
          previous.set(next.id, { from: current, type: next.type, songs: next.songs });
          queue.push(next.id);
        }
      }
    }
    if (!previous.has(endId)) return null;

    const steps = [];
    let node = endId;
    while (node !== null) {
      const info = previous.get(node);
      steps.unshift({ id: node, type: info ? info.type : null, songs: info ? info.songs : 0 });
      node = info ? info.from : null;
    }
    return steps;
  }

  function showPath(steps) {
    draw(
      [
        ...steps.map((step, i) => ({
          data: { id: step.id, label: nameById.get(step.id), kind: "path" },
          position: { x: i * 170, y: (i % 2) * 60 },
        })),
        ...steps.slice(1).map((step, i) => ({
          data: { id: "p" + i, source: steps[i].id, target: step.id, songs: step.songs, label: shortLabel(step) },
        })),
      ],
      { name: "preset" }
    );

    chain.replaceChildren();
    steps.forEach((step, i) => {
      if (i > 0) {
        const connector = document.createElement("li");
        connector.className = "connector";
        connector.textContent = "\u2193 " + describeStep(step);
        chain.appendChild(connector);
      }
      const li = document.createElement("li");
      li.className = "artist";
      li.appendChild(nameButton(step.id));
      chain.appendChild(li);
    });

    lists.hidden = true;
    legend.hidden = true;
    chain.hidden = false;
  }

  function pathSummary(steps) {
    const a = nameById.get(steps[0].id);
    const b = nameById.get(steps[steps.length - 1].id);
    const links = steps.length - 1;
    if (links === 1) return `${a} and ${b} are directly connected.`;
    const through = steps.slice(1, -1).map((step) => nameById.get(step.id));
    return `${a} and ${b} are ${links} steps apart, through ${through.join(" and ")}.`;
  }

  relatedForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const id = idByName.get(simplify(inputOne.value));
    if (!id) {
      result.textContent = "That name isn't in the data. Pick from the suggestions.";
      return;
    }
    showRelated(id);
  });

  pathForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const startId = idByName.get(simplify(inputA.value));
    const endId = idByName.get(simplify(inputB.value));

    if (!startId || !endId) {
      result.textContent = "One of those names isn't in the data. Pick from the suggestions.";
      return;
    }

    const steps = findPath(startId, endId);
    if (!steps) {
      result.textContent = "No connection found in the data.";
      return;
    }

    if (steps.length === 1) {
      result.textContent = "That's the same artist.";
      return;
    }

    showPath(steps);
    result.textContent = pathSummary(steps);
  });

  cy.on("tap", "node", (event) => {
    showRelated(event.target.id());
  });

  result.textContent = `${data.nodes.length} artists loaded. Try one of the two tools above.`;
}