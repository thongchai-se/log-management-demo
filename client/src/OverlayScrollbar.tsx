import { useEffect, useRef, useState, type RefObject } from 'react'

type Props = {
  targetRef: RefObject<HTMLElement | null>
}

/** Floating scrollbar over the scroll target — never steals layout width. */
export function OverlayScrollbar({ targetRef }: Props) {
  const trackRef = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)
  const [metrics, setMetrics] = useState({ top: 0, height: 0, visible: false })

  useEffect(() => {
    const el = targetRef.current
    if (!el) return

    const update = () => {
      const view = el.clientHeight
      const total = el.scrollHeight
      if (total <= view + 1) {
        setMetrics({ top: 0, height: 0, visible: false })
        return
      }
      const height = Math.max(32, (view / total) * view)
      const maxTop = view - height
      const top = maxTop * (el.scrollTop / (total - view))
      setMetrics({ top, height, visible: true })
    }

    update()
    el.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update)
    const ro = new ResizeObserver(update)
    ro.observe(el)
    if (el.firstElementChild) ro.observe(el.firstElementChild)

    return () => {
      el.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
      ro.disconnect()
    }
  }, [targetRef])

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      const el = targetRef.current
      if (!dragging.current || !trackRef.current || !el) return
      const rect = trackRef.current.getBoundingClientRect()
      const view = el.clientHeight
      const total = el.scrollHeight
      const thumb = Math.max(32, (view / total) * view)
      const maxTop = view - thumb
      const y = e.clientY - rect.top - thumb / 2
      const ratio = Math.min(1, Math.max(0, y / maxTop))
      el.scrollTop = ratio * (total - view)
    }
    const onUp = () => {
      dragging.current = false
      document.body.style.userSelect = ''
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [targetRef])

  if (!metrics.visible) return null

  return (
    <div
      ref={trackRef}
      className="overlay-scrollbar"
      aria-hidden="true"
      onPointerDown={(e) => {
        const el = targetRef.current
        if (!el || !trackRef.current) return
        if ((e.target as HTMLElement).dataset.thumb === '1') return
        const rect = trackRef.current.getBoundingClientRect()
        const view = el.clientHeight
        const total = el.scrollHeight
        const ratio = Math.min(1, Math.max(0, (e.clientY - rect.top) / view))
        el.scrollTop = ratio * (total - view)
      }}
    >
      <div
        className="overlay-scrollbar-thumb"
        data-thumb="1"
        style={{ height: metrics.height, transform: `translateY(${metrics.top}px)` }}
        onPointerDown={(e) => {
          e.preventDefault()
          e.stopPropagation()
          dragging.current = true
          document.body.style.userSelect = 'none'
        }}
      />
    </div>
  )
}
