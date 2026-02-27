const base = ''

export async function listPapers(params = {}) {
  const q = new URLSearchParams(params).toString()
  const r = await fetch(`${base}/api/papers?${q}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getPaper(id) {
  const r = await fetch(`${base}/api/papers/${id}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function uploadPdf(file) {
  const fd = new FormData()
  fd.append('file', file)
  const r = await fetch(`${base}/api/papers/upload`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function fromArxiv(body) {
  const r = await fetch(`${base}/api/papers/from-arxiv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function triggerInterpret(paperId) {
  const r = await fetch(`${base}/api/papers/${paperId}/interpret`, { method: 'POST' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getInterpretation(paperId) {
  const r = await fetch(`${base}/api/papers/${paperId}/interpretation`)
  if (!r.ok) throw new Error(await r.text())
  return r.text()
}

export async function triggerPodcast(paperId) {
  const r = await fetch(`${base}/api/papers/${paperId}/podcast`, { method: 'POST' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getTask(taskId) {
  const r = await fetch(`${base}/api/tasks/${taskId}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function deletePaper(paperId) {
  const r = await fetch(`${base}/api/papers/${paperId}`, { method: 'DELETE' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getRelated(paperId) {
  const r = await fetch(`${base}/api/papers/${paperId}/related`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getCollectSettings() {
  const r = await fetch(`${base}/api/settings/collect`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function updateCollectSettings(body) {
  const r = await fetch(`${base}/api/settings/collect`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getKnowledgeGraph() {
  const r = await fetch(`${base}/api/knowledge-graph`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getTrending() {
  const r = await fetch(`${base}/api/trending`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export function podcastUrl(paperId) {
  return `${base}/api/papers/${paperId}/podcast`
}
