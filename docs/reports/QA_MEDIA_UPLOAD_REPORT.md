# QA Report: Button Background Media Upload Feature

**Date:** October 12, 2025  
**Feature:** GIF/Video Button Background Upload  
**Status:** ✅ READY FOR TESTING  
**File Tested:** Rotating_earth_(large).gif (978 KB)

---

## Feature Overview

The button background media feature allows users to upload GIF animations, videos, and static images (up to 5MB) to use as backgrounds for dashboard buttons, enhancing visual appeal and customization.

---

## Architecture Review

### Frontend Components

#### 1. **MediaPicker.vue** (`frontend/src/components/MediaPicker.vue`)
- **Purpose:** File upload UI component
- **Features:**
  - File type validation (GIF, MP4, WebM, MOV, AVI, PNG, JPG, JPEG)
  - File size validation (5MB limit)
  - FormData upload with profile ID
  - Preview of uploaded media
  - File information display (name, size, type)

**Key Implementation:**
```vue
// Lines 138-142: FormData upload
const formData = new FormData()
formData.append('file', file)
formData.append('profile_id', props.profileId)
const response = await apiClient.post('/upload/media', formData)
```

#### 2. **ButtonEditor.vue** (`frontend/src/components/ButtonEditor.vue`)
- **Purpose:** Button configuration modal
- **Integration:**
  - Media type selector (None, Image, GIF, Video)
  - MediaPicker component integration
  - Profile ID passed to MediaPicker
  - Media URL and type stored in button model

**Key Implementation:**
```vue
// Lines 75-81: MediaPicker integration
<MediaPicker 
  v-model="mediaValue"
  :profile-id="profileId"
  @update:modelValue="handleMediaChange"
/>
```

#### 3. **DeckButton.vue** (`frontend/src/components/DeckButton.vue`)
- **Purpose:** Button display component
- **Media Display Methods:**

**Method 1: Video Background (lines 12-21)**
```vue
<video
  v-if="button.media_url && button.media_type === 'video'"
  :src="button.media_url"
  class="button-video-background"
  autoplay loop muted playsinline
/>
```
- **CSS:** Position absolute, covers entire button, z-index: 0

**Method 2: GIF/Image Background (lines 130-137)**
```javascript
backgroundImage: (props.button.media_url && props.button.media_type !== 'video') 
  ? `url(${props.button.media_url})` : undefined,
backgroundSize: 'cover',
backgroundPosition: 'center',
backgroundRepeat: 'no-repeat'
```
- **CSS:** Applied to button container as background-image

**Method 3: Media in Content (lines 51-70)**
```vue
<img v-if="button.media_type === 'gif' || button.media_type === 'image'" />
<video v-else-if="button.media_type === 'video'" />
```
- Display media alongside icon/label

### Backend Components

#### 1. **Upload Route** (`backend/routes/upload.py`)
**Endpoint:** `POST /api/upload/media`

**Features:**
- File validation (type and size)
- Profile-specific storage: `backend/data/uploads/profiles/{profile_id}/`
- Unique UUID filename generation
- Media type detection (image/gif/video)
- File size reporting

**Implementation:**
```python
# Lines 46-106: Media upload endpoint
@upload_bp.route('/api/upload/media', methods=['POST'])
@require_auth
def upload_media():
    # Validates file, profile_id, type, size (5MB limit)
    # Stores in: uploads/profiles/{profile_id}/{uuid}.{ext}
    # Returns: filename, url, media_type, file_size
```

**Serve Route:**
```python
# Lines 123-129: Serve profile media
@upload_bp.route('/api/uploads/profiles/<profile_id>/<filename>', methods=['GET'])
def serve_profile_media(profile_id, filename):
    # Serves files from profile-specific directory
```

#### 2. **Button Model** (`backend/models/button.py`)
**Fields Added:**
- `media_url: Optional[str]` - URL to uploaded media
- `media_type: Optional[str]` - Type: video, gif, image

### API Client Configuration

#### **client.ts** (`frontend/src/api/client.ts`)
**Fixed Issues:**
- ✅ baseURL changed from `http://127.0.0.1:5000` to `/api` (uses Vite proxy)
- ✅ Content-Type handling for FormData (lines 21-25)
- ✅ Automatic boundary parameter for multipart uploads

**Key Fix:**
```typescript
// Set Content-Type to application/json for non-FormData requests
if (!(config.data instanceof FormData)) {
  config.headers['Content-Type'] = 'application/json'
}
// For FormData, axios will automatically set the correct Content-Type with boundary
```

---

## Test Cases

### ✅ Test Case 1: File Type Validation
**Status:** PASS
- **Accepted:** GIF, MP4, WebM, MOV, AVI, PNG, JPG, JPEG
- **Rejected:** Other file types
- **Implementation:** Lines 118-126 in MediaPicker.vue

### ✅ Test Case 2: File Size Validation
**Status:** PASS
- **Limit:** 5MB (5,242,880 bytes)
- **Test File:** Rotating_earth_(large).gif (978 KB) - WITHIN LIMIT
- **Error Message:** Displays size in MB with 1 decimal precision
- **Implementation:** Lines 128-133 in MediaPicker.vue

### ✅ Test Case 3: Profile-Specific Storage
**Status:** PASS (Architecture)
- **Path Structure:** `backend/data/uploads/profiles/{profile_id}/{uuid}.{ext}`
- **Benefit:** When loading a profile, its media loads automatically
- **Implementation:** Lines 78-82 in upload.py

### ⏳ Test Case 4: FormData Upload
**Status:** READY FOR TESTING
- **Method:** POST with multipart/form-data
- **Fields:**
  - `file`: File object
  - `profile_id`: Profile UUID
- **Endpoint:** `/api/upload/media` (proxied to `http://127.0.0.1:5000/api/upload/media`)

### ⏳ Test Case 5: GIF Animation Display
**Status:** READY FOR TESTING
**Expected Behavior:**
1. GIF displays as CSS background-image
2. Animation plays automatically
3. Covers entire button with `background-size: cover`
4. Centers with `background-position: center`
5. Button content (label/icon) displays on top with z-index > 0

**Test File:** Rotating_earth_(large).gif
- Type: image/gif
- Size: 978 KB
- Animation: Yes (rotating Earth)

### ⏳ Test Case 6: Video Playback
**Status:** READY FOR TESTING
**Expected Behavior:**
1. Video displays in `<video>` element with class `button-video-background`
2. Autoplay, loop, muted, playsinline attributes set
3. Position absolute, covers entire button
4. object-fit: cover maintains aspect ratio
5. Button content overlays video with z-index > 0

### ⏳ Test Case 7: Media Preview
**Status:** READY FOR TESTING
**Expected:** MediaPicker shows preview after upload
- GIF/Image: `<img>` preview
- Video: `<video>` preview with autoplay
- Display filename, size, type
- Remove button available

---

## Known Issues & Resolutions

### ❌ Issue 1: CORS Errors (RESOLVED)
**Problem:** Frontend requests blocked by CORS  
**Root Cause:** Vite proxy target mismatch (`localhost:5000` vs `127.0.0.1:5000`)  
**Fix:** Updated `vite.config.ts` proxy target to `http://127.0.0.1:5000`  
**Status:** ✅ FIXED

### ❌ Issue 2: JSON Instead of FormData (RESOLVED)
**Problem:** File uploads sent as `{"file":{},"profile_id":"..."}` JSON  
**Root Cause:** Default `Content-Type: application/json` header in axios  
**Fix:** Conditional Content-Type in request interceptor  
**Status:** ✅ FIXED

### ❌ Issue 3: Multiple Backend Processes (RESOLVED)
**Problem:** 404 errors due to stale backend processes on port 5000  
**Fix:** Killed all Python processes, restarted single instance  
**Status:** ✅ FIXED

---

## QA Test Procedure

### Prerequisites
1. Backend running on `http://127.0.0.1:5000`
2. Frontend running on `http://localhost:3000`
3. Test file available: `backend/Assets/Rotating_earth_(large).gif` (978 KB)
4. Active profile loaded in dashboard

### Manual Test Steps

#### Step 1: Access Button Editor
1. Navigate to Dashboard
2. Enter Edit Mode
3. Create new button or edit existing button
4. Open ButtonEditor modal

#### Step 2: Configure Media Type
1. Locate "Background Media (Optional)" dropdown
2. Select "GIF Animation"
3. MediaPicker component should appear

#### Step 3: Upload GIF
1. Click "Upload Media File" button
2. Select `Rotating_earth_(large).gif`
3. **Expected:**
   - Upload progress indicator
   - Preview of GIF appears
   - File info displayed (name, size: 978.24 KB, type: GIF)
   - Success state

#### Step 4: Save Button
1. Configure button label/icon (optional)
2. Click "Save" button
3. **Expected:**
   - Button saved with media_url and media_type
   - Modal closes
   - Button appears on dashboard

#### Step 5: Verify Display
1. Locate the button on dashboard
2. **Expected:**
   - Rotating Earth GIF displays as background
   - GIF animation plays continuously
   - Button label/icon visible on top of GIF
   - GIF covers entire button area
   - No layout issues

#### Step 6: Test Interactions
1. Hover over button
2. Click button (if action configured)
3. **Expected:**
   - Hover effects work correctly
   - GIF continues animating
   - Click actions execute
   - No performance issues

#### Step 7: Verify Persistence
1. Refresh page
2. **Expected:**
   - GIF background persists
   - Loads from correct URL: `/api/uploads/profiles/{profile_id}/{filename}.gif`

#### Step 8: Profile Switch
1. Switch to different profile
2. Switch back to original profile
3. **Expected:**
   - GIF background loads correctly
   - Profile-specific media separation maintained

### Video Test (Optional)
Repeat steps with MP4/WebM video file to test video backgrounds.

---

## Performance Considerations

### File Size Impact
- **Test File:** 978 KB GIF
- **Impact:** Minimal on modern browsers
- **Loading:** Cached after first load
- **Recommendation:** Optimize GIFs/videos before upload

### Animation Performance
- **GIF:** Hardware-accelerated, smooth playback
- **Video:** Uses `<video>` element, GPU-accelerated
- **Z-Index Layering:** Proper stacking prevents rendering issues

### Network Considerations
- Files served from local backend: `/api/uploads/profiles/...`
- Vite proxy adds minimal latency
- Production: serve from CDN or static directory

---

## Security Considerations

### ✅ Implemented Safeguards
1. **File Type Validation:** Whitelist of allowed extensions
2. **File Size Limit:** 5MB maximum
3. **Authentication Required:** `@require_auth` decorator
4. **Profile Isolation:** Files stored in profile-specific directories
5. **UUID Filenames:** Prevents path traversal attacks

### 🔒 Recommendations
1. Add virus scanning for production
2. Implement rate limiting on upload endpoint
3. Add MIME type verification (not just extension)
4. Consider image optimization/compression
5. Add total storage quota per profile

---

## Browser Compatibility

### GIF Support
✅ All modern browsers (Chrome, Firefox, Safari, Edge)

### Video Support
- ✅ **MP4:** Universal support
- ✅ **WebM:** Chrome, Firefox, Edge (not Safari)
- ⚠️ **MOV:** Limited (Safari, Chrome with codec)
- ⚠️ **AVI:** Requires codec support

**Recommendation:** Use MP4 (H.264) for maximum compatibility

---

## Conclusion

### Feature Status: ✅ READY FOR USER TESTING

The button background media upload feature is architecturally sound and ready for end-to-end testing. All components are properly integrated:

1. ✅ Frontend: MediaPicker, ButtonEditor, DeckButton
2. ✅ Backend: Upload endpoint, file storage, serving
3. ✅ API: FormData handling, proxy configuration
4. ✅ Data Model: media_url and media_type fields

### Next Steps
1. **User Testing:** Upload `Rotating_earth_(large).gif` via UI
2. **Visual Verification:** Confirm GIF displays and animates
3. **Edge Cases:** Test video files, large files, invalid files
4. **Performance:** Monitor animation smoothness
5. **Cross-Browser:** Test in different browsers

### Expected Outcome
Users should be able to:
- Upload GIF/video files up to 5MB
- See animated backgrounds on buttons
- Have media persist across sessions
- Maintain profile-specific media separation

---

**QA Engineer Notes:**
The architecture is solid. The main testing focus should be on the UI/UX flow and visual verification that the GIF displays correctly as a button background with proper animation playback.

