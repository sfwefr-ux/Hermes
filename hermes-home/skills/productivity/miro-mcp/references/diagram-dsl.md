# Diagram DSL Reference (from diagram_get_dsl)

## Common Rules (all diagram types)

- Direction: `graphdir TB|LR|BT|RL` on first line
- Node IDs: `n1`, `n2`, `n3`...
- Edge IDs: `e1`, `e2`, `e3`... (though flowchart uses `c` prefix for connectors)
- One element per line — don't split across lines

## Flowchart DSL

### Palette
```
palette #fff6b6 #c6dcff #adf0c7
```
Default: `#fff6b6` (yellow, processes), `#c6dcff` (blue, decisions), `#adf0c7` (green, terminators)

### Nodes
```
n<id> <label> <object> <color_index>
```
Objects: `flowchart-process`, `flowchart-decision`, `flowchart-terminator`, `flowchart-data`

### Connectors
```
c <source_node_id> <label> <target_node_id>
```
- Use `-` for empty label
- Use `YES`/`NO` for decision branches

### Clusters
```
cluster c<id> "<label>" <node_id1> <node_id2> ...
```
- MUST be at end of DSL (after all nodes and edges)
- A node can belong to at most one cluster

### Full Example
```
graphdir LR
palette #fff6b6 #c6dcff #adf0c7

n1 Start flowchart-terminator 2
n2 Process flowchart-process 0
n3 Decide? flowchart-decision 1
n4 Action A flowchart-process 0
n5 Action B flowchart-process 0
n6 Done flowchart-terminator 2

c n1 - n2
c n2 - n3
c n3 YES n4
c n3 NO n5
c n4 - n6
c n5 - n6

cluster c1 "Phase 1" n1 n2
cluster c2 "Phase 2" n3 n4 n5
cluster c3 "Phase 3" n6
```

## Custom Colors (from allowed list)

`#ffc6c6`, `#f8d3af`, `#fff6b6`, `#dbfaad`, `#adf0c7`, `#c3faf5`, `#ccf4ff`, `#c6dcff`, `#dedaff`, `#ffd8f4`, `#e7e7e7`
