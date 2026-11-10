// vdock-audio-tap: stream the Mac's mixed system output audio to stdout.
//
// Uses a Core Audio process tap (macOS 14.2+) - the supported way to hear
// "what the speakers are playing" without a virtual driver such as BlackHole.
// The Python spectrum service (services/macos_audio_tap.py) spawns this and
// feeds the samples to the same FFT pipeline the Windows loopback uses.
//
// Wire format on stdout:
//   4 bytes   sample rate, UInt32 little-endian
//   then      mono Float32 little-endian samples, forever
//
// Failures go to stderr as one line and exit non-zero. Build:
//   swiftc -O vdock_audio_tap.swift -o vdock-audio-tap

import AudioToolbox
import CoreAudio
import Foundation

func fail(_ message: String, status: OSStatus = 0) -> Never {
    let line = "vdock-audio-tap: \(message) (OSStatus \(status))\n"
    FileHandle.standardError.write(Data(line.utf8))
    exit(1)
}

func readProperty<Value>(
    of objectID: AudioObjectID,
    selector: AudioObjectPropertySelector,
    into value: inout Value
) -> OSStatus {
    var address = AudioObjectPropertyAddress(
        mSelector: selector,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain
    )
    var size = UInt32(MemoryLayout<Value>.size)
    return AudioObjectGetPropertyData(objectID, &address, 0, nil, &size, &value)
}

func defaultOutputDeviceUID() -> String {
    var deviceID = AudioObjectID(kAudioObjectUnknown)
    let deviceStatus = readProperty(
        of: AudioObjectID(kAudioObjectSystemObject),
        selector: kAudioHardwarePropertyDefaultSystemOutputDevice,
        into: &deviceID
    )
    guard deviceStatus == noErr, deviceID != kAudioObjectUnknown else {
        fail("no default output device", status: deviceStatus)
    }

    var uid: CFString = "" as CFString
    let uidStatus = readProperty(of: deviceID, selector: kAudioDevicePropertyDeviceUID, into: &uid)
    guard uidStatus == noErr else {
        fail("cannot read output device UID", status: uidStatus)
    }
    return uid as String
}

func writeToStdout(_ bytes: UnsafeRawPointer, count: Int) {
    fwrite(bytes, 1, count, stdout)
    fflush(stdout)
}

@available(macOS 14.2, *)
func runTap() -> Never {
    let tapDescription = CATapDescription(stereoGlobalTapButExcludeProcesses: [])
    tapDescription.name = "VDock spectrum"
    tapDescription.isPrivate = true
    tapDescription.muteBehavior = .unmuted

    var tapID = AudioObjectID(kAudioObjectUnknown)
    let tapStatus = AudioHardwareCreateProcessTap(tapDescription, &tapID)
    guard tapStatus == noErr else {
        fail("cannot create system audio tap", status: tapStatus)
    }

    let outputUID = defaultOutputDeviceUID()
    let aggregateDescription: [String: Any] = [
        kAudioAggregateDeviceNameKey: "VDock spectrum tap",
        kAudioAggregateDeviceUIDKey: UUID().uuidString,
        kAudioAggregateDeviceMainSubDeviceKey: outputUID,
        kAudioAggregateDeviceIsPrivateKey: true,
        kAudioAggregateDeviceIsStackedKey: false,
        kAudioAggregateDeviceTapAutoStartKey: true,
        kAudioAggregateDeviceSubDeviceListKey: [
            [kAudioSubDeviceUIDKey: outputUID]
        ],
        kAudioAggregateDeviceTapListKey: [
            [
                kAudioSubTapDriftCompensationKey: true,
                kAudioSubTapUIDKey: tapDescription.uuid.uuidString,
            ]
        ],
    ]

    var aggregateID = AudioObjectID(kAudioObjectUnknown)
    let aggregateStatus = AudioHardwareCreateAggregateDevice(aggregateDescription as CFDictionary, &aggregateID)
    guard aggregateStatus == noErr else {
        fail("cannot create aggregate device", status: aggregateStatus)
    }

    var format = AudioStreamBasicDescription()
    let formatStatus = readProperty(of: tapID, selector: kAudioTapPropertyFormat, into: &format)
    guard formatStatus == noErr, format.mSampleRate > 0, format.mChannelsPerFrame > 0 else {
        fail("cannot read tap format", status: formatStatus)
    }
    guard format.mFormatID == kAudioFormatLinearPCM, format.mBitsPerChannel == 32,
          (format.mFormatFlags & kAudioFormatFlagIsFloat) != 0 else {
        fail("unsupported tap format (expected 32-bit float PCM)")
    }

    let isInterleaved = (format.mFormatFlags & kAudioFormatFlagIsNonInterleaved) == 0
    let channelCount = Int(format.mChannelsPerFrame)

    var sampleRate = UInt32(format.mSampleRate.rounded()).littleEndian
    writeToStdout(&sampleRate, count: MemoryLayout<UInt32>.size)

    var monoBuffer = [Float](repeating: 0, count: 8192)
    let ioQueue = DispatchQueue(label: "vdock.audio-tap.io", qos: .userInteractive)
    var ioProcID: AudioDeviceIOProcID?
    let ioStatus = AudioDeviceCreateIOProcIDWithBlock(&ioProcID, aggregateID, ioQueue) { _, inputData, _, _, _ in
        let buffers = UnsafeMutableAudioBufferListPointer(UnsafeMutablePointer(mutating: inputData))
        guard let firstBuffer = buffers.first, let firstData = firstBuffer.mData else { return }

        let frameCount: Int
        if isInterleaved {
            frameCount = Int(firstBuffer.mDataByteSize) / (MemoryLayout<Float>.size * channelCount)
        } else {
            frameCount = Int(firstBuffer.mDataByteSize) / MemoryLayout<Float>.size
        }
        guard frameCount > 0 else { return }
        if frameCount > monoBuffer.count {
            monoBuffer = [Float](repeating: 0, count: frameCount)
        }

        if isInterleaved {
            let samples = firstData.assumingMemoryBound(to: Float.self)
            for frame in 0..<frameCount {
                var sum: Float = 0
                for channel in 0..<channelCount {
                    sum += samples[frame * channelCount + channel]
                }
                monoBuffer[frame] = sum / Float(channelCount)
            }
        } else {
            for frame in 0..<frameCount { monoBuffer[frame] = 0 }
            for buffer in buffers {
                guard let data = buffer.mData else { continue }
                let samples = data.assumingMemoryBound(to: Float.self)
                for frame in 0..<min(frameCount, Int(buffer.mDataByteSize) / MemoryLayout<Float>.size) {
                    monoBuffer[frame] += samples[frame] / Float(buffers.count)
                }
            }
        }
        monoBuffer.withUnsafeBytes { writeToStdout($0.baseAddress!, count: frameCount * MemoryLayout<Float>.size) }
    }
    guard ioStatus == noErr, let procID = ioProcID else {
        fail("cannot create IO proc", status: ioStatus)
    }

    let startStatus = AudioDeviceStart(aggregateID, procID)
    guard startStatus == noErr else {
        fail("cannot start audio tap", status: startStatus)
    }

    func shutDown() -> Never {
        AudioDeviceStop(aggregateID, procID)
        AudioDeviceDestroyIOProcID(aggregateID, procID)
        AudioHardwareDestroyAggregateDevice(aggregateID)
        AudioHardwareDestroyProcessTap(tapID)
        exit(0)
    }

    for terminationSignal in [SIGTERM, SIGINT] {
        signal(terminationSignal, SIG_IGN)
        let source = DispatchSource.makeSignalSource(signal: terminationSignal, queue: .main)
        source.setEventHandler { shutDown() }
        source.resume()
        signalSources.append(source)
    }

    dispatchMain()
}

var signalSources: [DispatchSourceSignal] = []

if #available(macOS 14.2, *) {
    runTap()
} else {
    fail("system audio capture needs macOS 14.2 or newer")
}
