'use client';

/**
 * VoiceCommandButton Component
 *
 * Microphone button for activating voice commands
 * Features:
 * - Start/stop voice recording
 * - Visual recording state (pulsing animation)
 * - Microphone permission handling
 * - Browser compatibility detection
 * - Interim and final transcript display
 * - Success/error feedback
 * - Bilingual support (English/Urdu)
 */

import { useState, useCallback } from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useVoiceCommands } from '@/hooks/useVoiceCommands';
import { isSpeechRecognitionSupported } from '@/lib/voice/featureDetection';
import type { VoiceCommand } from '@/types/voice';
import { cn } from '@/lib/utils';

export interface VoiceCommandButtonProps {
  onCommand: (command: VoiceCommand) => void | Promise<void>;
  className?: string;
  showTranscript?: boolean;
  disabled?: boolean;
}

export function VoiceCommandButton({
  onCommand,
  className,
  showTranscript = true,
  disabled = false,
}: VoiceCommandButtonProps) {
  const t = useTranslations('voice');
  const [feedback, setFeedback] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  // Voice command hook with command callback
  const {
    state,
    startRecording,
    stopRecording,
    requestPermission,
  } = useVoiceCommands(async (command) => {
    try {
      await onCommand(command);
      setFeedback({
        type: 'success',
        message: t('command_recognized'),
      });
      // Clear feedback after 3 seconds
      setTimeout(() => setFeedback({ type: null, message: '' }), 3000);
    } catch (error) {
      setFeedback({
        type: 'error',
        message: error instanceof Error ? error.message : 'Command failed',
      });
      // Clear feedback after 5 seconds
      setTimeout(() => setFeedback({ type: null, message: '' }), 5000);
    }
  });

  // Check browser support
  const isSupported = isSpeechRecognitionSupported();

  // Handle button click
  const handleClick = useCallback(async () => {
    if (!isSupported) {
      setFeedback({
        type: 'error',
        message: t('not_supported'),
      });
      return;
    }

    if (state.isRecording) {
      stopRecording();
    } else {
      // Request permission if needed
      if (state.permissionStatus === 'prompt') {
        const granted = await requestPermission();
        if (!granted) {
          setFeedback({
            type: 'error',
            message: t('permission_denied'),
          });
          return;
        }
      }

      if (state.permissionStatus === 'denied') {
        setFeedback({
          type: 'error',
          message: t('permission_denied'),
        });
        return;
      }

      // Start recording
      await startRecording();
    }
  }, [
    isSupported,
    state.isRecording,
    state.permissionStatus,
    startRecording,
    stopRecording,
    requestPermission,
    t,
  ]);

  // Determine button state
  const isRecording = state.isRecording;
  const hasError = state.error !== null || feedback.type === 'error';
  const isDisabled = disabled || !isSupported || state.isProcessing;

  return (
    <div className={cn('relative flex flex-col items-center gap-2', className)}>
      {/* Voice Command Button */}
      <button
        type="button"
        onClick={handleClick}
        disabled={isDisabled}
        className={cn(
          'relative inline-flex items-center justify-center rounded-full transition-all duration-300',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          isRecording
            ? 'w-16 h-16 bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/50 animate-pulse focus:ring-red-500'
            : hasError
            ? 'w-14 h-14 bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 border-2 border-red-500/50 focus:ring-red-500'
            : 'w-14 h-14 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-600 dark:text-indigo-400 border-2 border-indigo-500/50 hover:scale-110 focus:ring-indigo-500'
        )}
        aria-label={isRecording ? t('listening') : t('enable_microphone')}
        title={isRecording ? t('listening') : t('speak_command')}
      >
        {isRecording ? (
          <MicOff className="w-6 h-6" />
        ) : hasError ? (
          <AlertCircle className="w-6 h-6" />
        ) : (
          <Mic className="w-6 h-6" />
        )}

        {/* Recording pulse effect */}
        {isRecording && (
          <span className="absolute inset-0 rounded-full bg-red-500 opacity-75 animate-ping" />
        )}
      </button>

      {/* Status Text */}
      {isRecording && (
        <span className="text-sm font-medium text-red-600 dark:text-red-400 animate-pulse">
          {t('listening')}
        </span>
      )}

      {/* Interim Transcript Display */}
      {showTranscript && isRecording && state.interimTranscript && (
        <div className="glass-card px-4 py-2 rounded-lg border border-indigo-500/30 max-w-md">
          <p className="text-sm text-gray-600 dark:text-gray-400 italic">
            {state.interimTranscript}
          </p>
        </div>
      )}

      {/* Final Transcript Display (Processing) */}
      {showTranscript && state.isProcessing && state.finalTranscript && (
        <div className="glass-card px-4 py-2 rounded-lg border border-indigo-500/30 max-w-md">
          <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
            {state.finalTranscript}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {t('processing')}
          </p>
        </div>
      )}

      {/* Success/Error Feedback */}
      {feedback.type && (
        <div
          className={cn(
            'glass-card px-4 py-2 rounded-lg border max-w-md',
            feedback.type === 'success'
              ? 'border-green-500/30 bg-green-500/10'
              : 'border-red-500/30 bg-red-500/10'
          )}
        >
          <p
            className={cn(
              'text-sm font-medium',
              feedback.type === 'success'
                ? 'text-green-700 dark:text-green-300'
                : 'text-red-700 dark:text-red-300'
            )}
          >
            {feedback.message}
          </p>
        </div>
      )}

      {/* Error Display */}
      {state.error && (
        <div className="glass-card px-4 py-2 rounded-lg border border-red-500/30 bg-red-500/10 max-w-md">
          <p className="text-sm font-medium text-red-700 dark:text-red-300">
            {state.error.message}
          </p>
        </div>
      )}

      {/* Browser Not Supported Warning */}
      {!isSupported && (
        <div className="glass-card px-4 py-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 max-w-md">
          <p className="text-sm font-medium text-yellow-700 dark:text-yellow-300">
            {t('not_supported')}
          </p>
        </div>
      )}
    </div>
  );
}
