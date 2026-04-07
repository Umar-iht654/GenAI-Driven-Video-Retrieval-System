// Import hooks used to access the video DOM element and track internal player state
import { useEffect, useRef, useState } from 'react'

// Import helpers for displaying timestamps nicely
import { formatSegmentRange, formatTimestamp } from '../utils/timestamps'

// Import video source helpers so the app can map video ids to actual files
import { DEFAULT_VIDEO_ID, getVideoConfig } from '../utils/videoSources'

// Define the video player component that shows and controls the selected lecture clip
function VideoPlayer({ request }) {
  // Store a direct reference to the HTML video element
  const videoRef = useRef(null)

  // Store the next playback request without forcing an immediate re-render
  const pendingRequestRef = useRef(null)

  // Store the end time of the selected clip so playback can stop near that point
  const clipEndRef = useRef(null)

  // Store any player error message shown in the UI
  const [playerError, setPlayerError] = useState('')

  // Track which video is currently loaded into the player
  const [activeVideoId, setActiveVideoId] = useState(DEFAULT_VIDEO_ID)

  // Track whether the video is currently playing
  const [isPlaying, setIsPlaying] = useState(false)

  // Get the selected segment from the incoming request
  const selectedSegment = request?.segment ?? null

  // Resolve the current video id into a display label and file source path
  const activeVideoConfig = getVideoConfig(activeVideoId)

  // Apply the pending playback request to the actual HTML video element
  const applyPlaybackRequest = () => {
    const video = videoRef.current
    const pendingRequest = pendingRequestRef.current

    // If there is no player element or no request waiting, do nothing
    if (!video || !pendingRequest) {
      return
    }

    const { segment, shouldPlaySegment } = pendingRequest

    // Store the clip end time so playback can stop automatically later
    clipEndRef.current = Number.isFinite(segment.end) ? segment.end : null

    // Jump the video to the selected segment start time
    video.currentTime = Math.max(0, segment.start)

    // If playback was requested, try to play the clip, otherwise just pause at the selected time
    if (shouldPlaySegment) {
      void video.play().catch(() => {
        setPlayerError(
          'The browser blocked autoplay for the selected clip. Press play to continue.'
        )
      })
    } else {
      video.pause()
    }

    // Clear the pending request once it has been applied
    pendingRequestRef.current = null
  }

  // Update the current request whenever a new segment is selected
  useEffect(() => {
    if (!request?.segment) {
      return
    }

    // Store the request for later application
    pendingRequestRef.current = request

    // Clear any previous player error
    setPlayerError('')

    // Switch the currently loaded video if the selected segment belongs to a different lecture
    setActiveVideoId(request.segment.videoId || DEFAULT_VIDEO_ID)
  }, [request])

  // Re-apply the playback request once the correct video is loaded and ready
  useEffect(() => {
    if (!request?.segment || request.segment.videoId !== activeVideoId) {
      return
    }

    // If metadata is already loaded, apply the request immediately
    if (videoRef.current?.readyState >= 1) {
      applyPlaybackRequest()
    }
  }, [activeVideoId, request])

  // During playback, stop the video near the requested clip end time
  const handleTimeUpdate = () => {
    const video = videoRef.current

    // If there is no player or no clip end time, do nothing
    if (!video || clipEndRef.current === null) {
      return
    }

    // If the current playback position reaches the clip end, stop playback and hold at the end frame
    if (video.currentTime >= clipEndRef.current) {
      video.pause()
      video.currentTime = clipEndRef.current
      clipEndRef.current = null
    }
  }

  // Handle clicking the overlay button to play the selected clip
  const handlePlayClip = () => {
    if (!selectedSegment) {
      return
    }

    // Create a new request that tells the player to play the segment immediately
    pendingRequestRef.current = {
      segment: selectedSegment,
      shouldPlaySegment: true,
    }

    // If the video is already ready, apply the request right away
    if (videoRef.current?.readyState >= 1) {
      applyPlaybackRequest()
    }
  }

  return (
    <section className="video-player">
      {/* Top bar showing clip label and current selected segment range */}
      <div className="video-player__header">
        <p className="video-player__eyebrow">Clip Preview</p>
        <div className="video-player__stats">
          <span>{selectedSegment?.videoId ?? activeVideoId}</span>
          <span>
            {selectedSegment ? formatSegmentRange(selectedSegment) : 'No clip selected'}
          </span>
        </div>
      </div>

      {/* Frame containing the actual video element and overlay controls */}
      <div className="video-player__frame">
        <video
          key={activeVideoConfig.src}
          ref={videoRef}
          className="video-player__element"
          controls
          preload="metadata"
          src={activeVideoConfig.src}
          onLoadedMetadata={applyPlaybackRequest}
          onTimeUpdate={handleTimeUpdate}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
          onError={() =>
            setPlayerError(
              'This video could not be loaded. Check that the lecture file exists and matches the video_id mapping.'
            )
          }
        />

        {/* If a segment exists, show overlay controls and badges */}
        {selectedSegment ? (
          <>
            <button
              type="button"
              className="video-player__play-overlay"
              onClick={handlePlayClip}
            >
              {isPlaying ? 'Restart clip' : 'Play clip'}
            </button>

            <div className="video-player__badge">
              {formatTimestamp(selectedSegment.start)}
            </div>

            <div className="video-player__badge video-player__badge--secondary">
              {activeVideoConfig.label}
            </div>
          </>
        ) : (
          <div className="video-player__empty">
            No video clip is available for this response.
          </div>
        )}
      </div>

      {/* Explain where the selected clip starts and stops */}
      {selectedSegment ? (
        <p className="video-player__hint">
          This clip starts at {formatTimestamp(selectedSegment.start)} and will
          stop near {formatTimestamp(selectedSegment.end)} when clip playback is used.
        </p>
      ) : null}

      {/* Show any player error if video playback/loading fails */}
      {playerError ? <p className="video-player__error">{playerError}</p> : null}
    </section>
  )
}

// Export the component so Message.jsx can use it
export default VideoPlayer