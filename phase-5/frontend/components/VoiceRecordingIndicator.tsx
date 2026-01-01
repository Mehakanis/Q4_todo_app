'use client';

/**
 * VoiceRecordingIndicator Component
 *
 * Visual indicator for voice recording and speaking states
 * Features:
 * - Recording state (pulsing red dot)
 * - Speaking state (pulsing blue animation)
 * - Processing state (loading spinner)
 * - Minimalist design
 * - Accessible with ARIA labels
 */

import { useTranslations } from 'next-intl';
import { Mic, Volume2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface VoiceRecordingIndicatorProps {
  isRecording?: boolean;
  isSpeaking?: boolean;
  isProcessing?: boolean;
  className?: string;
  showLabel?: boolean;
}

export function VoiceRecordingIndicator({
  isRecording = false,
  isSpeaking = false,
  isProcessing = false,
  className,
  showLabel = true,
}: VoiceRecordingIndicatorProps) {
  const t = useTranslations('voice');

  // Determine which state to display (priority: recording > speaking > processing)
  const state = isRecording
    ? 'recording'
    : isSpeaking
    ? 'speaking'
    : isProcessing
    ? 'processing'
    : 'idle';

  // Don't render if idle
  if (state === 'idle') {
    return null;
  }

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-full transition-all duration-300',
        state === 'recording' &&
          'bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400',
        state === 'speaking' &&
          'bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400',
        state === 'processing' &&
          'bg-indigo-500/10 border border-indigo-500/30 text-indigo-600 dark:text-indigo-400',
        className
      )}
      role="status"
      aria-live="polite"
      aria-label={
        state === 'recording'
          ? t('listening')
          : state === 'speaking'
          ? 'Speaking'
          : t('processing')
      }
    >
      {/* State Icon */}
      {state === 'recording' && (
        <>
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-600" />
          </span>
          {showLabel && (
            <span className="text-sm font-medium animate-pulse">{t('listening')}</span>
          )}
        </>
      )}

      {state === 'speaking' && (
        <>
          <Volume2 className="w-4 h-4 animate-pulse" />
          {showLabel && <span className="text-sm font-medium">Speaking...</span>}
        </>
      )}

      {state === 'processing' && (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          {showLabel && <span className="text-sm font-medium">{t('processing')}</span>}
        </>
      )}
    </div>
  );
}

/**
 * VoiceRecordingWaveform Component
 *
 * Animated waveform visualization for voice recording
 * Provides visual feedback during active recording
 */

export interface VoiceRecordingWaveformProps {
  isActive?: boolean;
  className?: string;
}

export function VoiceRecordingWaveform({
  isActive = false,
  className,
}: VoiceRecordingWaveformProps) {
  if (!isActive) {
    return null;
  }

  return (
    <div
      className={cn('flex items-center gap-1 h-8', className)}
      role="img"
      aria-label="Voice recording waveform animation"
    >
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-red-500 rounded-full animate-pulse"
          style={{
            height: `${20 + Math.random() * 60}%`,
            animationDelay: `${i * 0.1}s`,
            animationDuration: `${0.5 + Math.random() * 0.5}s`,
          }}
        />
      ))}
    </div>
  );
}
