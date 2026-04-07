export const DEFAULT_VIDEO_ID = 'Lec1'

export function getVideoConfig(videoId) {
  const safeVideoId = videoId || DEFAULT_VIDEO_ID
  const hasExtension = /\.[a-z0-9]+$/i.test(safeVideoId)

  return {
    label: safeVideoId,
    src: `/videos/${hasExtension ? safeVideoId : `${safeVideoId}.mp4`}`,
  }
}