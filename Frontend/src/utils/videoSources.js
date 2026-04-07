export const DEFAULT_VIDEO_ID = 'Lec1'

const VIDEO_SOURCE_MAP = {
  Lec1: {
    label: 'Lecture 1',
    src: '/videos/Lec1.mp4',
  },
}

export function getVideoConfig(videoId) {
  if (!videoId) {
    return VIDEO_SOURCE_MAP[DEFAULT_VIDEO_ID]
  }

  const mappedVideo = VIDEO_SOURCE_MAP[videoId]

  if (mappedVideo) {
    return mappedVideo
  }

  const hasExtension = /\.[a-z0-9]+$/i.test(videoId)

  return {
    label: videoId,
    src: `/videos/${hasExtension ? videoId : `${videoId}.mp4`}`,
  }
}
