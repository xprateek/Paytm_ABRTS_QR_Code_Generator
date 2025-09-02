<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import QRCode from 'qrcode'


/* ---------------- Theme ---------------- */
const theme = ref('system') // 'system' | 'light' | 'dark'
const showMenu = ref(false)
const mql = window.matchMedia?.('(prefers-color-scheme: dark)')
const isDark = computed(() => theme.value === 'dark' || (theme.value === 'system' && mql?.matches))
function setTheme(v) { theme.value = v; showMenu.value = false; persist() }


/* ---------------- State from JSON ---------------- */
const config = ref(null)
const inputText = ref('')
const sizeOptions = ref([])
const selectedSize = ref(256)
const errorCorrectionLevels = ref([])
const selectedECL = ref('M')


/* ---------------- Preset behavior ---------------- */
const selectedPreset = ref('') // preset name; empty when not set
const textLockedByPreset = computed(() => !!selectedPreset.value)


/* ---------------- QR generation ---------------- */
const qrDataUrl = ref('')
const qrLabelDataUrl = ref('')

// Generate plain QR Data URL (for preview without label)
async function generateQRCode() {
  try {
    const text = (inputText.value || '').trim()
    if (!text) {
      qrDataUrl.value = ''
      qrLabelDataUrl.value = ''
      return
    }
    qrDataUrl.value = await QRCode.toDataURL(text, {
      width: Number(selectedSize.value),
      margin: 2,
      errorCorrectionLevel: selectedECL.value,
      color: {
        dark: isDark.value ? '#e5e7eb' : '#111827',
        light: isDark.value ? '#111827' : '#ffffff'
      }
    })
    qrLabelDataUrl.value = await generateLabeledQR()
  } catch {
    qrDataUrl.value = ''
    qrLabelDataUrl.value = ''
  }
}

// Generate QR code with label (station name) below, merged on canvas as PNG data URL
async function generateLabeledQR() {
  const label = selectedStationName.value.trim() || 'Station'
  const size = Number(selectedSize.value)
  const margin = 16
  const font = '16px Arial'
  const labelPadding = 4

  // Create a canvas sized for QR + label below
  const canvas = document.createElement('canvas')

  // Calculate label text width to ensure canvas width fits label and QR code (whichever is wider)
  const textWidth = measureTextWidth(label, font)
  const width = Math.max(size, textWidth + margin * 2)
  const height = size + margin + 24 + labelPadding // QR code + margin + label height + padding

  canvas.width = width
  canvas.height = height

  const ctx = canvas.getContext('2d')

  // Draw background - light/dark mode
  ctx.fillStyle = isDark.value ? '#111827' : '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // Generate QR code image to draw
  const qrImgData = await QRCode.toDataURL(inputText.value, {
    width: size,
    margin: 2,
    errorCorrectionLevel: selectedECL.value,
    color: {
      dark: isDark.value ? '#e5e7eb' : '#111827',
      light: isDark.value ? '#111827' : '#ffffff'
    }
  })
  const qrImg = new Image()
  qrImg.src = qrImgData
  await new Promise((res) => { qrImg.onload = res })

  // Draw QR code centered horizontally
  ctx.drawImage(qrImg, (width - size) / 2, 0)

  // Draw label below QR code
  ctx.font = font
  ctx.fillStyle = isDark.value ? '#e5e7eb' : '#111827'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.fillText(label, width / 2, size + margin + labelPadding)

  return canvas.toDataURL('image/png')
}

// Measure text width helper (used for canvas sizing)
function measureTextWidth(text, font) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.font = font
  return ctx.measureText(text).width
}


/* ---------------- Persistence ---------------- */
const STORAGE_KEY = 'qr-studio:state'
function persist() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        theme: theme.value,
        inputText: inputText.value,
        selectedSize: selectedSize.value,
        selectedECL: selectedECL.value,
        selectedPreset: selectedPreset.value
      })
    )
  } catch {}
}
function restore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const data = JSON.parse(raw)
    if (data.theme) theme.value = data.theme
    if (typeof data.inputText === 'string') inputText.value = data.inputText
    if (data.selectedSize) selectedSize.value = data.selectedSize
    if (data.selectedECL) selectedECL.value = data.selectedECL
    if (data.selectedPreset) selectedPreset.value = data.selectedPreset
  } catch {}
}


/* ---------------- JSON validation (no editor) ---------------- */
const jsonError = ref('')


function isString(v) { return typeof v === 'string' }
function isArray(v) { return Array.isArray(v) }
function isObject(v) { return v && typeof v === 'object' && !Array.isArray(v) }


function validateConfig(obj) {
  if (!isObject(obj)) return 'Config must be a JSON object'
  if ('defaultText' in obj && obj.defaultText != null && !isString(obj.defaultText)) {
    return 'defaultText must be a string'
  }
  if ('sizes' in obj) {
    if (!isArray(obj.sizes)) return 'sizes must be an array'
    for (const [i, it] of obj.sizes.entries()) {
      if (!isObject(it) || !isString(it.label) || typeof it.value !== 'number') {
        return `sizes[${i}] must be {label:string, value:number}`
      }
    }
  }
  if ('errorCorrections' in obj) {
    if (!isArray(obj.errorCorrections)) return 'errorCorrections must be an array'
    for (const [i, it] of obj.errorCorrections.entries()) {
      if (!isObject(it) || !isString(it.label) || !isString(it.value)) {
        return `errorCorrections[${i}] must be {label:string, value:string}`
      }
    }
  }
  if ('presets' in obj) {
    if (!isArray(obj.presets)) return 'presets must be an array'
    for (const [i, it] of obj.presets.entries()) {
      if (!isObject(it) || !isString(it.name)) return `presets[${i}] must include name:string`
      if ('text' in it && !isString(it.text)) return `presets[${i}].text must be a string`
      if ('size' in it && typeof it.size !== 'number') return `presets[${i}].size must be a number`
      if ('ecl' in it && !isString(it.ecl)) return `presets[${i}].ecl must be a string`
    }
  }
  return ''
}


async function loadConfig() {
  jsonError.value = ''
  try {
    const res = await fetch('/input.json', { cache: 'no-cache' })
    if (!res.ok) throw new Error(`Failed to fetch /input.json (${res.status})`)
    const text = await res.text()
    let obj
    try { obj = JSON.parse(text) } catch (e) { throw new Error(`JSON parse error: ${e.message}`) }
    const err = validateConfig(obj)
    if (err) throw new Error(err)

    config.value = obj
    if (!inputText.value) inputText.value = obj.defaultText || ''
    sizeOptions.value = obj.sizes?.length ? obj.sizes : [
      { label: 'Medium (256x256)', value: 256 },
      { label: 'Large (512x512)', value: 512 }
    ]
    errorCorrectionLevels.value = obj.errorCorrections?.length ? obj.errorCorrections : [
      { label: 'Medium (M)', value: 'M' },
      { label: 'High (H)', value: 'H' }
    ]
    if (!sizeOptions.value.some(o => o.value === selectedSize.value)) {
      selectedSize.value = sizeOptions.value[0].value
    }
    if (!errorCorrectionLevels.value.some(o => o.value === selectedECL.value)) {
      selectedECL.value = errorCorrectionLevels.value.value
    }
  } catch (e) {
    jsonError.value = `input.json error: ${e.message}`
    // Safe fallbacks to keep app functional
    config.value = {
      defaultText: 'Hello',
      sizes: [
        { label: 'Medium (256x256)', value: 256 },
        { label: 'Large (512x512)', value: 512 }
      ],
      errorCorrections: [
        { label: 'Medium (M)', value: 'M' },
        { label: 'High (H)', value: 'H' }
      ],
      presets: []
    }
    if (!inputText.value) inputText.value = config.value.defaultText
    sizeOptions.value = config.value.sizes
    errorCorrectionLevels.value = config.value.errorCorrections
    selectedSize.value = 256
    selectedECL.value = 'M'
  }
}


/* ---------------- Dropdown manager (single-open) ---------------- */
const openId = ref('') // '', 'size', 'ecl', 'presets'
function toggleOpen(id) { openId.value = openId.value === id ? '' : id }
function closeAll() { openId.value = ''; stationSearch.value = '' }
const sizeOpen = computed(() => openId.value === 'size')
const eclOpen = computed(() => openId.value === 'ecl')
const ddOpen = computed(() => openId.value === 'presets')


const ddActiveIndex = ref(0)
const sizeActiveIndex = ref(0)
const eclActiveIndex = ref(0)


const sizeLabel = computed(() => {
  const found = sizeOptions.value.find(o => o.value === selectedSize.value)
  return found ? found.label : 'Select size…'
})
const eclLabel = computed(() => {
  const found = errorCorrectionLevels.value.find(o => o.value === selectedECL.value)
  return found ? found.label : 'Select error correction…'
})


function applyPresetByName(name) {
  if (!config.value?.presets?.length) return
  const p = config.value.presets.find(x => x.name === name)
  if (!p) return
  selectedPreset.value = p.name
  inputText.value = p.text ?? inputText.value
  if (p.size) selectedSize.value = p.size
  if (p.ecl) selectedECL.value = p.ecl
  stationSearch.value = ''
}


/* Presets search box state */
const stationSearch = ref("")


const filteredPresets = computed(() => {
  if (!config.value?.presets?.length) return []
  if (!stationSearch.value.trim()) return config.value.presets
  return config.value.presets.filter(p =>
    p.name.toLowerCase().includes(stationSearch.value.toLowerCase())
  )
})


/* Presets keyboard + choose (updated to work with filtered list) */
function ddNext() {
  if (!filteredPresets.value.length) return
  if (!ddOpen.value) toggleOpen('presets')
  ddActiveIndex.value = (ddActiveIndex.value + 1) % filteredPresets.value.length
}
function ddPrev() {
  if (!filteredPresets.value.length) return
  if (!ddOpen.value) toggleOpen('presets')
  ddActiveIndex.value = (ddActiveIndex.value - 1 + filteredPresets.value.length) % filteredPresets.value.length
}
function ddCommit() {
  const preset = filteredPresets.value[ddActiveIndex.value]
  if (!preset) return
  const idx = config.value.presets.findIndex(p => p.name === preset.name)
  ddChoose(idx)
}
function ddChoose(i) {
  const p = config.value.presets[i]
  if (!p) return
  applyPresetByName(p.name)
  closeAll()
  persist()
}


/* Size keyboard + choose */
function sizeNext() {
  if (!sizeOptions.value.length) return
  if (!sizeOpen.value) toggleOpen('size')
  sizeActiveIndex.value = (sizeActiveIndex.value + 1) % sizeOptions.value.length
}
function sizePrev() {
  if (!sizeOptions.value.length) return
  if (!sizeOpen.value) toggleOpen('size')
  sizeActiveIndex.value = (sizeActiveIndex.value - 1 + sizeOptions.value.length) % sizeOptions.value.length
}
function sizeCommit() { sizeChoose(sizeActiveIndex.value) }
function sizeChoose(i) {
  const opt = sizeOptions.value[i]
  if (!opt) return
  selectedSize.value = opt.value
  closeAll()
  persist()
}


/* ECL keyboard + choose */
function eclNext() {
  if (!errorCorrectionLevels.value.length) return
  if (!eclOpen.value) toggleOpen('ecl')
  eclActiveIndex.value = (eclActiveIndex.value + 1) % errorCorrectionLevels.value.length
}
function eclPrev() {
  if (!errorCorrectionLevels.value.length) return
  if (!eclOpen.value) toggleOpen('ecl')
  eclActiveIndex.value = (eclActiveIndex.value - 1 + errorCorrectionLevels.value.length) % errorCorrectionLevels.value.length
}
function eclCommit() { eclChoose(eclActiveIndex.value) }
function eclChoose(i) {
  const opt = errorCorrectionLevels.value[i]
  if (!opt) return
  selectedECL.value = opt.value
  closeAll()
  persist()
}


/* Close when clicking outside any .dd */
function onDocumentClick(e) {
  const inside = e.target.closest?.('.dd')
  if (!inside) closeAll()
}


/* ---------------- Effects ---------------- */
watch([inputText, selectedSize, selectedECL, isDark], () => {
  generateQRCode()
  persist()
})


onMounted(async () => {
  restore()
  await loadConfig()
  await generateQRCode()
  mql?.addEventListener?.('change', onSystemThemeChange)
  document.addEventListener('click', onDocumentClick)
})
onBeforeUnmount(() => {
  mql?.removeEventListener?.('change', onSystemThemeChange)
  document.removeEventListener('click', onDocumentClick)
})
function onSystemThemeChange() {
  if (theme.value === 'system') generateQRCode()
}


/* UI helper */
function clearPresetAndText() {
  selectedPreset.value = ''
  inputText.value = ''
  stationSearch.value = ''
  persist()
}


/* For warning line: get selected station name from preset */
const selectedStationName = computed(() => {
  if (!selectedPreset.value) return ''
  const p = config.value?.presets?.find(x => x.name === selectedPreset.value)
  return p?.name ?? ''
})

// Computed property to provide dynamic download filename including station name
const computedDownloadName = computed(() => {
  const station = selectedStationName.value.trim() || 'qr-code'
  const safeName = station.replace(/\s+/g, '_').replace(/[^\w\-]/g, '')
  return `${safeName}.png`
})

// Method to force download via a created anchor element (to avoid some browser quirks)
function downloadImageWithLabel() {
  const link = document.createElement('a')
  link.href = qrLabelDataUrl.value
  link.download = computedDownloadName.value
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<template>
  <div :class="['app', { dark: isDark }]">
    <!-- Header -->
    <header class="header">
      <div class="brand">
        <span class="logo">🔳</span>
        <span class="title">Open Source QR Code Generator</span>
      </div>

      <div class="actions">
        <div class="dropdown" @keydown.escape="showMenu = false">
          <button class="btn" @click="showMenu = !showMenu" aria-haspopup="menu" :aria-expanded="showMenu">
            Menu ▾
          </button>
          <div v-if="showMenu" class="menu" role="menu">
            <button class="menu-item" role="menuitem" @click="setTheme('system')">System theme</button>
            <button class="menu-item" role="menuitem" @click="setTheme('light')">Light theme</button>
            <button class="menu-item" role="menuitem" @click="setTheme('dark')">Dark theme</button>
          </div>
        </div>
      </div>
    </header>

    <!-- Error banner (if input.json invalid) -->
    <div v-if="jsonError" class="alert">
      <strong>Config error:</strong> {{ jsonError }}
    </div>

    <!-- Main -->
    <main class="page">
      <section class="card">
        <h2>Paytm A-BRTS QR Code Generator</h2>

        <!-- Presets first -->
        <div class="row" v-if="config?.presets?.length">
          <div class="col">
            <label class="label">Select BRTS Bus Station</label>

            <div class="dd" @keydown.escape="closeAll()" @keydown.down.prevent="ddNext()" @keydown.up.prevent="ddPrev()"
              @keydown.enter.prevent="ddCommit()">
              <button class="dd-btn" type="button" :aria-expanded="ddOpen" aria-haspopup="listbox"
                @click="toggleOpen('presets')">
                <span>{{ selectedPreset || 'Select preset…' }}</span>
                <span class="dd-arrow" :class="{ open: ddOpen }" aria-hidden="true">▾</span>
              </button>

              <ul v-if="ddOpen" class="dd-menu" role="listbox">
                <!-- Search box -->
                <li class="dd-search">
                  <input
                    type="text"
                    v-model="stationSearch"
                    placeholder="Search station..."
                    class="input search-input"
                    @keydown.stop
                  />
                </li>

                <!-- Filtered results -->
                <li
                  v-for="(p, i) in filteredPresets"
                  :id="`opt-${i}`"
                  :key="p.name"
                  class="dd-item"
                  :class="{ active: i === ddActiveIndex }"
                  role="option"
                  :aria-selected="p.name === selectedPreset"
                  @click="() => { ddChoose(config.presets.findIndex(x => x.name === p.name)) }"
                  @mousemove="ddActiveIndex = i"
                >
                  {{ p.name }}
                </li>

                <!-- Empty state -->
                <li v-if="!filteredPresets.length" class="dd-item disabled">No station found</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Size + ECL -->
        <div class="row">
          <!-- Size -->
          <div class="col">
            <label class="label">Size</label>
            <div class="dd" @keydown.escape="closeAll()" @keydown.down.prevent="sizeNext()"
              @keydown.up.prevent="sizePrev()" @keydown.enter.prevent="sizeCommit()">
              <button class="dd-btn" type="button" :aria-expanded="sizeOpen" aria-haspopup="listbox"
                @click="toggleOpen('size')">
                <span>{{ sizeLabel }}</span>
                <span class="dd-arrow" :class="{ open: sizeOpen }" aria-hidden="true">▾</span>
              </button>

              <ul v-if="sizeOpen" class="dd-menu" role="listbox" :aria-activedescendant="`size-opt-${sizeActiveIndex}`">
                <li v-for="(opt, i) in sizeOptions" :id="`size-opt-${i}`" :key="opt.value" class="dd-item"
                  :class="{ active: i === sizeActiveIndex }" role="option" :aria-selected="opt.value === selectedSize"
                  @click="sizeChoose(i)" @mousemove="sizeActiveIndex = i">
                  {{ opt.label }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Error correction -->
          <div class="col">
            <label class="label">Error correction</label>
            <div class="dd" @keydown.escape="closeAll()" @keydown.down.prevent="eclNext()"
              @keydown.up.prevent="eclPrev()" @keydown.enter.prevent="eclCommit()">
              <button class="dd-btn" type="button" :aria-expanded="eclOpen" aria-haspopup="listbox"
                @click="toggleOpen('ecl')">
                <span>{{ eclLabel }}</span>
                <span class="dd-arrow" :class="{ open: eclOpen }" aria-hidden="true">▾</span>
              </button>

              <ul v-if="eclOpen" class="dd-menu" role="listbox" :aria-activedescendant="`ecl-opt-${eclActiveIndex}`">
                <li v-for="(opt, i) in errorCorrectionLevels" :id="`ecl-opt-${i}`" :key="opt.value" class="dd-item"
                  :class="{ active: i === eclActiveIndex }" role="option" :aria-selected="opt.value === selectedECL"
                  @click="eclChoose(i)" @mousemove="eclActiveIndex = i">
                  {{ opt.label }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div class="preview" aria-live="polite">
          <div class="qr-wrap" v-if="qrDataUrl">
            <img :src="qrDataUrl" :alt="`QR code for: ${inputText}`" />
          </div>
          <div class="empty" v-else>QR Code Preview</div>
        </div>

        <!-- Text to encode (disabled if preset chosen) -->
        <label class="label">Text to encode</label>
        <div class="input-row">
          <input class="input" :disabled="textLockedByPreset" type="text" placeholder="QR Code Encode Preview"
            v-model="inputText" />
          <button v-if="textLockedByPreset" class="mini-btn" @click="clearPresetAndText()"
            title="Clear preset to edit text">
            Unlock
          </button>
        </div>

        <!-- Warning: show only when a QR is generated -->
        <p class="warn">
          Scan this code only when physically present at {{ selectedStationName || 'the selected' }} station
        </p>

        <div class="buttons">
          <a
            v-if="qrLabelDataUrl"
            :href="qrLabelDataUrl"
            :download="computedDownloadName"
            class="btn primary"
            @click.prevent="downloadImageWithLabel"
          >
            Download PNG
          </a>
          <button class="btn" @click="inputText = ''; selectedPreset = '';">Clear</button>
        </div>
      </section>
    </main>

    <footer class="footer"><a href="http://prateekspace.eu.org/"> Prateek Maru</a> • ©2025 • <a
        href="https://github.com/xprateek/Paytm_ABRTS_QR_Code_Generator">Source Code</a> • Made with ❤️ Vue 3</footer>
  </div>
</template>

<style scoped>
/* Theme tokens on .app and .app.dark */
.app {
  --bg: #ffffff;
  --card: #f8fafc;
  --text: #111827;
  --muted: #6b7280;
  --border: #e5e7eb;
  --primary: #2563eb;
  --primary-contrast: #ffffff;

  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  width: 100%;
  display: grid;
  grid-template-rows: auto 1fr auto;
  overflow-x: hidden;
}

.app.dark {
  --bg: #0b1220;
  --card: #0f172a;
  --text: #e5e7eb;
  --muted: #94a3b8;
  --border: #1f2937;
  --primary: #60a5fa;
  --primary-contrast: #0b1220;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.logo {
  font-size: 20px;
}

.title {
  font-size: 16px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dropdown {
  position: relative;
}

.menu {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  min-width: 200px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  padding: 6px;
  display: grid;
}

.menu-item {
  text-align: left;
  background: transparent;
  border: none;
  color: var(--text);
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.menu-item:hover {
  background: rgba(99, 102, 241, 0.1);
}

/* Error banner */
.alert {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
  padding: 10px 14px;
  margin: 12px auto 0;
  border-radius: 10px;
  max-width: 1100px;
}

/* Page + Card */
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  max-width: 720px;
  margin: 24px auto;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.25);
}

h2 {
  margin: 0 0 16px;
  font-size: 24px;
}

/* Labels/inputs */
.label {
  display: block;
  font-size: 14px;
  color: var(--muted);
  margin-top: 14px;
  margin-bottom: 7px;
}

.input-row {
  position: relative;
  display: flex;
  gap: 8px;
  align-items: center;
}

.input {
  flex: 1 1 auto;
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 10px 12px;
  border-radius: 10px;
  outline: none;
  transition: border-color .15s ease, box-shadow .15s ease, opacity .15s ease;
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--primary) 25%, transparent);
}

.input:disabled {
  opacity: .7;
  cursor: not-allowed;
}

/* Small unlock button when preset locks input */
.mini-btn {
  background: color-mix(in oklab, var(--primary) 12%, var(--bg));
  color: var(--text);
  border: 1px solid color-mix(in oklab, var(--border) 80%, transparent);
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.mini-btn:hover {
  background: color-mix(in oklab, var(--primary) 20%, var(--bg));
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.col {
  min-width: 0;
}

/* Preview */
.preview {
  margin-top: 18px;
  display: grid;
  place-items: center;
  padding: 18px;
  background: var(--bg);
  border: 1px dashed var(--border);
  border-radius: 12px;
}

.qr-wrap img {
  display: block;
  width: 100%;
  height: auto;
  max-width: 512px;
  border-radius: 12px;
}

.empty {
  color: var(--muted);
  font-size: 14px;
}

/* Buttons */
.buttons {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}

.btn.primary {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--primary-contrast);
}

.btn:hover {
  opacity: 0.9;
}

/* Footer */
.footer {
  border-top: 1px solid var(--border);
  padding: 12px 20px;
  font-size: 12px;
  color: var(--muted);
  text-align: center;
}

/* ---------- Custom dropdown (shared for Size, ECL, Presets) ---------- */
.dd {
  position: relative;
}

/* Trigger button with chevron */
.dd-btn {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: color-mix(in oklab, var(--bg) 92%, transparent);
  color: var(--text);
  border: 1px solid color-mix(in oklab, var(--border) 85%, transparent);
  padding: 12px 14px;
  border-radius: 14px;
  cursor: pointer;
  font-weight: 600;
  transition: border-color .15s ease, box-shadow .15s ease, background .15s ease;
}

.dd-btn:hover {
  border-color: color-mix(in oklab, var(--primary) 40%, var(--border));
}

.dd-btn:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px color-mix(in oklab, var(--primary) 22%, transparent);
}

/* Arrow with rotation animation */
.dd-arrow {
  display: inline-block;
  color: color-mix(in oklab, var(--text) 70%, transparent);
  font-size: 16px;
  line-height: 1;
  transform: translateY(1px) rotate(0deg);
  transform-origin: 50% 45%;
  transition: transform 160ms cubic-bezier(.2, .9, .2, 1), color 120ms ease;
}

.dd-arrow.open {
  transform: translateY(1px) rotate(180deg);
  color: var(--text);
}

.dd-btn:hover .dd-arrow,
.dd-btn:focus .dd-arrow {
  color: var(--text);
}

/* Popup menu: rounded with internal scrollbar */
.dd-menu {
  position: absolute;
  z-index: 20;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  max-height: 260px;
  overflow: auto;
  scrollbar-width: thin;
  list-style: none;
  margin: 0;
  padding: 6px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 18px 45px rgba(0, 0, 0, .28);
}

/* Custom scrollbar (WebKit) */
.dd-menu::-webkit-scrollbar {
  width: 10px;
}

.dd-menu::-webkit-scrollbar-track {
  background: color-mix(in oklab, var(--card) 85%, transparent);
  border-radius: 10px;
}

.dd-menu::-webkit-scrollbar-thumb {
  background: color-mix(in oklab, var(--text) 25%, transparent);
  border-radius: 10px;
}

.dd-menu::-webkit-scrollbar-thumb:hover {
  background: color-mix(in oklab, var(--text) 35%, transparent);
}

/* Items */
.dd-item {
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--text);
}

.dd-item:hover,
.dd-item.active {
  background: color-mix(in oklab, var(--primary) 12%, transparent);
}

.dd-item.disabled {
  color: var(--muted);
  cursor: not-allowed;
  background: transparent !important;
}

/* Search box inside dropdown */
.dd-search {
  padding: 6px;
}

.search-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-size: 14px;
}

.search-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--primary) 25%, transparent);
}

/* Dark-mode contrast */
.app.dark .dd-btn {
  background: color-mix(in oklab, var(--bg) 86%, transparent);
  border-color: color-mix(in oklab, var(--border) 70%, transparent);
}

/* Responsive */
@media (max-width: 640px) {
  .row {
    grid-template-columns: 1fr;
  }

  .page {
    padding: 20px 14px;
  }

  .card {
    padding: 18px;
    margin: 20px auto;
    border-radius: 16px;
  }
}

/* Remove underline from any button-styled links */
a.btn {
  text-decoration: none;
}

/* Extra safety: never underline primary button links on hover/focus/active */
a.btn.primary,
a.btn.primary:hover,
a.btn.primary:focus,
a.btn.primary:active {
  text-decoration: none;
}

/* If you still see underline due to user-agent styles, force it */
a.btn,
a.btn * {
  text-decoration: none !important;
}

.warn {
  margin-top: 10px;
  margin-bottom: 12px;
  padding: 8px 12px;
  text-align: center;
  font-size: 14px;
  border-radius: 8px;
  background: color-mix(in oklab, #eab308 15%, var(--card));
  /* subtle amber */
  border: 1px solid color-mix(in oklab, #eab308 35%, var(--border));
  color: var(--text);
}
</style>
