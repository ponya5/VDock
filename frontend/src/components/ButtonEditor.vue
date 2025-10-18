<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal button-editor">
      <div class="modal-header">
        <h2>Edit Button</h2>
        <div class="header-actions">
          <button class="save-profile-btn" @click="handleSaveProfile" title="Save Profile">
            <FontAwesomeIcon :icon="['fas', 'save']" />
          </button>
          <button class="close-btn" @click="emit('close')">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>
      </div>

      <div class="modal-body">
        <!-- Browse Actions Button -->
        <div class="form-group">
          <button class="btn btn-primary" @click="showActionsSidebar = true" style="width: 100%;">
            <FontAwesomeIcon :icon="['fas', 'list']" />
            Browse Button Actions
          </button>
        </div>

        <!-- FUNCTIONALITY SETTINGS (Top Priority) -->
        <div class="form-group">
          <label>Position</label>
          <div class="flex gap-sm">
            <div style="flex: 1">
              <label class="small-label">Row</label>
              <input v-model.number="editedButton.position.row" type="number" class="input" min="0" />
            </div>
            <div style="flex: 1">
              <label class="small-label">Column</label>
              <input v-model.number="editedButton.position.col" type="number" class="input" min="0" />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Size</label>
          <div class="flex gap-sm">
            <div style="flex: 1">
              <label class="small-label">Rows</label>
              <input v-model.number="editedButton.size.rows" type="number" class="input" min="1" max="3" />
            </div>
            <div style="flex: 1">
              <label class="small-label">Columns</label>
              <input v-model.number="editedButton.size.cols" type="number" class="input" min="1" max="3" />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Action Type</label>
          <div class="action-type-display">
            <span class="action-type-text">{{ getActionTypeDisplayName(actionType) }}</span>
            <span class="action-type-badge" :class="actionType || 'no-action'">
              {{ actionType || 'No Action' }}
            </span>
          </div>
        </div>

        <!-- Macro Configuration -->
        <div v-if="actionType === 'macro'" class="macro-editor">
          <div class="form-group">
            <label>Macro Steps</label>
            <div class="macro-builder-container">
              <!-- Visual Macro Builder -->
              <div class="macro-builder">
                <div class="macro-steps-display">
                  <div 
                    v-for="(step, index) in macroSteps" 
                    :key="index" 
                    class="macro-step-chip"
                    @click="editMacroStep(index)"
                  >
                    <span class="step-number">{{ index + 1 }}</span>
                    <span class="step-content">
                      <FontAwesomeIcon :icon="getStepIcon(step.type)" />
                      {{ getStepDescription(step) }}
                    </span>
                    <button class="remove-step" @click.stop="removeMacroStep(index)">
                      <FontAwesomeIcon :icon="['fas', 'times']" />
                    </button>
                  </div>
                  
                  <button class="add-step-btn" @click="showMacroStepSelector = true">
                    <FontAwesomeIcon :icon="['fas', 'plus']" />
                    Add Step
                  </button>
                </div>
              </div>

              <!-- Macro Step Selector -->
              <div v-if="showMacroStepSelector" class="macro-step-selector">
                <div class="selector-header">
                  <h4>Add Macro Step</h4>
                  <button class="close-selector" @click="showMacroStepSelector = false">
                    <FontAwesomeIcon :icon="['fas', 'times']" />
                  </button>
                </div>
                
                <div class="step-types">
                  <button 
                    class="step-type-btn"
                    @click="addMacroStep('hotkey')"
                  >
                    <FontAwesomeIcon :icon="['fas', 'keyboard']" />
                    <span>Hotkey</span>
                    <small>Send key combination</small>
                  </button>
                  
                  <button 
                    class="step-type-btn"
                    @click="addMacroStep('delay')"
                  >
                    <FontAwesomeIcon :icon="['fas', 'clock']" />
                    <span>Delay</span>
                    <small>Wait between actions</small>
                  </button>
                  
                  <button 
                    class="step-type-btn"
                    @click="addMacroStep('text')"
                  >
                    <FontAwesomeIcon :icon="['fas', 'keyboard']" />
                    <span>Type Text</span>
                    <small>Type text content</small>
                  </button>
                  
                  <button 
                    class="step-type-btn"
                    @click="addMacroStep('click')"
                  >
                    <FontAwesomeIcon :icon="['fas', 'mouse-pointer']" />
                    <span>Mouse Click</span>
                    <small>Click at coordinates</small>
                  </button>
                  
                  <button 
                    class="step-type-btn"
                    @click="addMacroStep('button')"
                  >
                    <FontAwesomeIcon :icon="['fas', 'square']" />
                    <span>Button Action</span>
                    <small>Execute existing button</small>
                  </button>
                </div>
              </div>

              <!-- Macro Step Editor -->
              <div v-if="editingStepIndex !== null" class="macro-step-editor">
                <div class="editor-header">
                  <h4>Edit Step {{ editingStepIndex + 1 }}</h4>
                  <button class="close-editor" @click="closeStepEditor">
                    <FontAwesomeIcon :icon="['fas', 'times']" />
                  </button>
                </div>
                
                <div class="step-editor-content">
                  <div v-if="macroSteps[editingStepIndex]?.type === 'hotkey'" class="form-group">
                    <label>Key Combination</label>
                    <div class="hotkey-selector-container">
                      <div class="hotkey-input-wrapper">
                        <input 
                          v-model="editingStep.keysString" 
                          type="text" 
                          class="input hotkey-input" 
                          placeholder="Click To Assign Via Keyboard Input"
                          readonly
                          @click="toggleMacroHotkeyDropdown"
                        />
                        <button 
                          class="dropdown-arrow" 
                          @click="toggleMacroHotkeyDropdown"
                          :class="{ 'open': showMacroHotkeyDropdown }"
                        >
                          <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
                        </button>
                      </div>
                      
                      <!-- Same hotkey dropdown as main hotkey editor -->
                      <div v-if="showMacroHotkeyDropdown" class="hotkey-dropdown">
                        <div class="hotkey-dropdown-header">
                          <h4>Manually Select Hotkeys</h4>
                        </div>
                        
                        <div class="hotkey-categories">
                          <!-- Letters and Numbers -->
                          <div class="hotkey-category">
                            <div class="category-header" @click="toggleMacroCategory('letters')">
                              <span>Letters And Numbers</span>
                              <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedMacroCategories.includes('letters') }" />
                            </div>
                            <div v-if="expandedMacroCategories.includes('letters')" class="category-content">
                              <div class="key-grid">
                                <button 
                                  v-for="key in letterKeys" 
                                  :key="key" 
                                  class="key-button"
                                  @click="addKeyToMacroCombination(key)"
                                >
                                  {{ key.toUpperCase() }}
                                </button>
                              </div>
                            </div>
                          </div>

                          <!-- Navigation Keys -->
                          <div class="hotkey-category">
                            <div class="category-header" @click="toggleMacroCategory('navigation')">
                              <span>Navigation Keys</span>
                              <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedMacroCategories.includes('navigation') }" />
                            </div>
                            <div v-if="expandedMacroCategories.includes('navigation')" class="category-content">
                              <div class="key-list">
                                <button 
                                  v-for="key in navigationKeys" 
                                  :key="key.value" 
                                  class="key-button"
                                  @click="addKeyToMacroCombination(key.value)"
                                >
                                  <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                                  {{ key.label }}
                                </button>
                              </div>
                            </div>
                          </div>

                          <!-- Function Keys -->
                          <div class="hotkey-category">
                            <div class="category-header" @click="toggleMacroCategory('function')">
                              <span>Function Keys</span>
                              <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedMacroCategories.includes('function') }" />
                            </div>
                            <div v-if="expandedMacroCategories.includes('function')" class="category-content">
                              <div class="key-grid">
                                <button 
                                  v-for="key in functionKeys" 
                                  :key="key" 
                                  class="key-button"
                                  @click="addKeyToMacroCombination(key)"
                                >
                                  {{ key.toUpperCase() }}
                                </button>
                              </div>
                            </div>
                          </div>

                          <!-- Modifier Keys -->
                          <div class="hotkey-category">
                            <div class="category-header" @click="toggleMacroCategory('modifiers')">
                              <span>Modifier Keys</span>
                              <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedMacroCategories.includes('modifiers') }" />
                            </div>
                            <div v-if="expandedMacroCategories.includes('modifiers')" class="category-content">
                              <div class="key-list">
                                <button 
                                  v-for="key in modifierKeys" 
                                  :key="key.value" 
                                  class="key-button modifier-key"
                                  @click="addKeyToMacroCombination(key.value)"
                                >
                                  <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                                  {{ key.label }}
                                </button>
                              </div>
                            </div>
                          </div>

                          <!-- Other Keys -->
                          <div class="hotkey-category">
                            <div class="category-header" @click="toggleMacroCategory('other')">
                              <span>Other Keys</span>
                              <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedMacroCategories.includes('other') }" />
                            </div>
                            <div v-if="expandedMacroCategories.includes('other')" class="category-content">
                              <div class="key-list">
                                <button 
                                  v-for="key in otherKeys" 
                                  :key="key.value" 
                                  class="key-button"
                                  @click="addKeyToMacroCombination(key.value)"
                                >
                                  <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                                  {{ key.label }}
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>

                        <!-- Current Combination Display -->
                        <div class="current-combination">
                          <div class="combination-label">Current Combination:</div>
                          <div class="combination-display">
                            <span 
                              v-for="(key, index) in currentMacroKeyCombination" 
                              :key="index" 
                              class="key-chip"
                            >
                              {{ key }}
                              <button class="remove-key" @click="removeKeyFromMacroCombination(index)">
                                <FontAwesomeIcon :icon="['fas', 'times']" />
                              </button>
                            </span>
                          </div>
                          <div class="combination-actions">
                            <button class="btn btn-secondary btn-sm" @click="clearMacroCombination">Clear All</button>
                            <button class="btn btn-primary btn-sm" @click="applyMacroCombination">Apply</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="macroSteps[editingStepIndex]?.type === 'delay'" class="form-group">
                    <label>Delay (milliseconds)</label>
                    <input 
                      v-model.number="editingStep.delay" 
                      type="number" 
                      class="input" 
                      placeholder="500"
                      min="0"
                      step="100"
                    />
                  </div>

                  <div v-if="macroSteps[editingStepIndex]?.type === 'text'" class="form-group">
                    <label>Text to Type</label>
                    <textarea 
                      v-model="editingStep.text" 
                      class="textarea" 
                      placeholder="Hello World"
                      rows="3"
                    ></textarea>
                  </div>

                  <div v-if="macroSteps[editingStepIndex]?.type === 'click'" class="form-group">
                    <label>Click Position</label>
                    <div class="flex gap-sm">
                      <input 
                        v-model.number="editingStep.clickX" 
                        type="number" 
                        class="input" 
                        placeholder="X coordinate"
                        min="0"
                      />
                      <input 
                        v-model.number="editingStep.clickY" 
                        type="number" 
                        class="input" 
                        placeholder="Y coordinate"
                        min="0"
                      />
                    </div>
                    <p class="form-help">Screen coordinates for mouse click</p>
                  </div>

                  <div v-if="macroSteps[editingStepIndex]?.type === 'button'" class="form-group">
                    <label>Select Button</label>
                    <div class="button-selector-container">
                      <div class="button-grid">
                        <div 
                          v-for="button in availableButtons" 
                          :key="button.id" 
                          class="button-option"
                          :class="{ 'selected': editingStep.buttonId === button.id }"
                          @click="selectButtonForMacro(button)"
                        >
                          <div class="button-preview">
                            <FontAwesomeIcon 
                              v-if="button.icon_type === 'fontawesome'" 
                              :icon="button.icon" 
                            />
                            <img 
                              v-else-if="button.icon_type === 'custom'" 
                              :src="button.icon" 
                              :alt="button.label"
                              class="custom-icon"
                            />
                          </div>
                          <div class="button-info">
                            <div class="button-label">{{ button.label }}</div>
                            <div class="button-action">{{ getButtonActionDescription(button) }}</div>
                          </div>
                        </div>
                      </div>
                      
                      <div v-if="availableButtons.length === 0" class="empty-state">
                        <FontAwesomeIcon :icon="['fas', 'info-circle']" />
                        <p>No buttons available to select. Create some buttons first.</p>
                      </div>
                    </div>
                    <p class="form-help">Click on a button to select it for this macro step</p>
                  </div>

                  <div class="editor-actions">
                    <button class="btn btn-secondary" @click="closeStepEditor">Cancel</button>
                    <button class="btn btn-primary" @click="saveStepEditor">Save</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- UI AND APPEARANCE SETTINGS (Bottom Priority) -->
        <div class="form-group">
          <label>Label</label>
          <input v-model="editedButton.label" type="text" class="input" placeholder="Button label" />
        </div>

        <div class="form-group">
          <label>Secondary Label (optional)</label>
          <input 
            v-model="editedButton.secondary_label" 
            type="text" 
            class="input" 
            placeholder="Secondary text"
          />
        </div>

        <div class="form-group">
          <label>Icon</label>
          <div class="flex gap-sm">
            <select v-model="editedButton.icon_type" class="select" style="flex: 1">
              <option value="fontawesome">FontAwesome Icon</option>
              <option value="custom">Custom Image</option>
            </select>
          </div>
        </div>

        <div v-if="editedButton.icon_type === 'fontawesome'" class="form-group">
          <label>FontAwesome Icon</label>
          <div class="flex gap-sm">
            <input 
              v-model="editedButton.icon" 
              type="text" 
              class="input" 
              placeholder="fas fa-home"
              style="flex: 1"
            />
            <button class="btn btn-secondary" @click="showAssetPicker = 'icon'">
              <FontAwesomeIcon :icon="['fas', 'icons']" /> Browse Icons
            </button>
          </div>
        </div>

        <div v-if="editedButton.icon_type === 'custom'" class="form-group">
          <label>Custom Image URL</label>
          <input 
            v-model="editedButton.icon" 
            type="text" 
            class="input" 
            placeholder="https://example.com/image.png"
          />
        </div>

        <div class="form-group">
          <label>Background Media (Optional)</label>
          <div class="flex gap-sm">
            <select v-model="editedButton.media_type" class="select" style="flex: 1">
              <option value="">No Background Media</option>
              <option value="image">Static Image</option>
              <option value="gif">GIF Animation</option>
              <option value="video">Video</option>
            </select>
            <button 
              v-if="editedButton.media_type" 
              class="btn btn-secondary" 
              @click="showAssetPicker = 'animation'"
            >
              <FontAwesomeIcon :icon="['fas', 'film']" /> Browse Media
            </button>
          </div>
        </div>

        <div v-if="editedButton.media_type && !showAssetPicker" class="form-group">
          <label>Background Media URL</label>
          <input 
            v-model="editedButton.media_url" 
            type="text" 
            class="input" 
            placeholder="Enter media URL or use Browse Media button"
          />
          <p class="form-help">
            {{ getMediaHelpText(editedButton.media_type) }}
          </p>
        </div>

        <div class="form-group">
          <label>Background Color</label>
          <div class="color-picker-section">
            <div class="current-color" :style="{ backgroundColor: editedButton.style?.backgroundColor || '#2c3e50' }">
              <input 
                v-model="editedButton.style.backgroundColor" 
                type="color" 
                class="color-input"
                @input="updateBackgroundColor"
              />
            </div>
            <div class="color-palette">
              <div 
                v-for="color in colorPalette" 
                :key="color"
                class="color-swatch"
                :class="{ active: editedButton.style?.backgroundColor === color }"
                :style="{ backgroundColor: color }"
                @click="selectColor(color)"
                :title="color"
              ></div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Icon Size</label>
          <div class="icon-size-controls">
            <input 
              v-model.number="editedButton.style.iconSize" 
              type="range" 
              class="icon-size-slider"
              min="16" 
              max="128" 
              step="4"
              @input="updateIconSize"
            />
            <div class="icon-size-display">
              <span>{{ editedButton.style?.iconSize || 32 }}px</span>
              <div class="icon-preview">
                <FontAwesomeIcon 
                  :icon="editedButton.icon || ['fas', 'home']" 
                  :style="{ fontSize: `${editedButton.style?.iconSize || 32}px` }"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Shape</label>
          <select v-model="editedButton.shape" class="select">
            <option value="rectangle">Rectangle</option>
            <option value="rounded">Rounded</option>
            <option value="circle">Circle</option>
            <option value="hexagon">Hexagon</option>
            <option value="diamond">Diamond</option>
            <option value="octagon">Octagon</option>
          </select>
        </div>

        <div class="form-group">
          <label>Visual Effects</label>
          <div class="flex gap-sm">
            <select v-model="editedButton.style.effect" class="select" style="flex: 1">
              <option value="none">None</option>
              <option value="glass">Glass Morphism</option>
              <option value="neumorphism">Neumorphism</option>
              <option value="gradient">Gradient</option>
              <option value="glow">Glow Effect</option>
              <option value="3d">3D Effect</option>
            </select>
            <button 
              class="btn btn-secondary" 
              @click="showAssetPicker = 'background'"
              title="Browse Background Assets"
            >
              <FontAwesomeIcon :icon="['fas', 'palette']" /> Backgrounds
            </button>
          </div>
        </div>

        <div v-if="editedButton.style?.effect === 'gradient'" class="form-group">
          <label>Custom Gradient</label>
          <input 
            v-model="editedButton.style.gradient" 
            type="text" 
            class="input" 
            placeholder="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
          />
        </div>

        <div class="form-group">
          <label>Animation</label>
          <select v-model="editedButton.style.animation" class="select">
            <option value="none">None</option>
            <option value="pulse">Pulse</option>
            <option value="shimmer">Shimmer</option>
            <option value="bounce">Bounce</option>
            <option value="rotate">Rotate</option>
          </select>
        </div>

        <!-- Action-specific configuration -->
        <div v-if="actionType === 'url'" class="form-group">
          <label>URL</label>
          <input v-model="actionConfig.url" type="text" class="input" placeholder="https://example.com" />
        </div>

        <div v-if="actionType === 'program'" class="form-group">
          <label>Program Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="C:\\Program Files\\..." />
        </div>

        <div v-if="actionType === 'command'" class="form-group">
          <label>Command</label>
          <textarea v-model="actionConfig.command" class="textarea" placeholder="echo Hello"></textarea>
        </div>

        <div v-if="actionType === 'hotkey'" class="form-group">
          <label>Hotkey Combination</label>
          <div class="hotkey-selector-container">
            <div class="hotkey-input-wrapper">
              <input 
                v-model="hotkeyString" 
                type="text" 
                class="input hotkey-input" 
                placeholder="Click To Assign Via Keyboard Input"
                readonly
                @click="toggleHotkeyDropdown"
              />
              <button 
                class="dropdown-arrow" 
                @click="toggleHotkeyDropdown"
                :class="{ 'open': showHotkeyDropdown }"
              >
                <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
              </button>
            </div>
            
            <!-- Hotkey Dropdown -->
            <div v-if="showHotkeyDropdown" class="hotkey-dropdown">
              <div class="hotkey-dropdown-header">
                <h4>Manually Select Hotkeys</h4>
              </div>
              
              <div class="hotkey-categories">
                <!-- Letters and Numbers -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('letters')">
                    <span>Letters And Numbers</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('letters') }" />
                  </div>
                  <div v-if="expandedCategories.includes('letters')" class="category-content">
                    <div class="key-grid">
                      <button 
                        v-for="key in letterKeys" 
                        :key="key" 
                        class="key-button"
                        @click="addKeyToCombination(key)"
                      >
                        {{ key.toUpperCase() }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Navigation Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('navigation')">
                    <span>Navigation Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('navigation') }" />
                  </div>
                  <div v-if="expandedCategories.includes('navigation')" class="category-content">
                    <div class="key-list">
                      <button 
                        v-for="key in navigationKeys" 
                        :key="key.value" 
                        class="key-button"
                        @click="addKeyToCombination(key.value)"
                      >
                        <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                        {{ key.label }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Function Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('function')">
                    <span>Function Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('function') }" />
                  </div>
                  <div v-if="expandedCategories.includes('function')" class="category-content">
                    <div class="key-grid">
                      <button 
                        v-for="key in functionKeys" 
                        :key="key" 
                        class="key-button"
                        @click="addKeyToCombination(key)"
                      >
                        {{ key.toUpperCase() }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Modifier Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('modifiers')">
                    <span>Modifier Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('modifiers') }" />
                  </div>
                  <div v-if="expandedCategories.includes('modifiers')" class="category-content">
                    <div class="key-list">
                      <button 
                        v-for="key in modifierKeys" 
                        :key="key.value" 
                        class="key-button modifier-key"
                        @click="addKeyToCombination(key.value)"
                      >
                        <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                        {{ key.label }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Other Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('other')">
                    <span>Other Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('other') }" />
                  </div>
                  <div v-if="expandedCategories.includes('other')" class="category-content">
                    <div class="key-list">
                      <button 
                        v-for="key in otherKeys" 
                        :key="key.value" 
                        class="key-button"
                        @click="addKeyToCombination(key.value)"
                      >
                        <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                        {{ key.label }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Current Combination Display -->
              <div class="current-combination">
                <div class="combination-label">Current Combination:</div>
                <div class="combination-display">
                  <span 
                    v-for="(key, index) in currentKeyCombination" 
                    :key="index" 
                    class="key-chip"
                  >
                    {{ key }}
                    <button class="remove-key" @click="removeKeyFromCombination(index)">
                      <FontAwesomeIcon :icon="['fas', 'times']" />
                    </button>
                  </span>
                </div>
                <div class="combination-actions">
                  <button class="btn btn-secondary btn-sm" @click="clearCombination">Clear All</button>
                  <button class="btn btn-primary btn-sm" @click="applyCombination">Apply</button>
                </div>
              </div>
            </div>
          </div>
          <p class="form-help">Click the dropdown to manually select keys, or use keyboard input for quick assignment</p>
        </div>

        <!-- Action-specific configuration -->
        <div v-if="actionType === 'url'" class="form-group">
          <label>URL</label>
          <input v-model="actionConfig.url" type="text" class="input" placeholder="https://example.com" />
        </div>

        <div v-if="actionType === 'program'" class="form-group">
          <label>Program Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="C:\\Program Files\\..." />
        </div>

        <div v-if="actionType === 'command'" class="form-group">
          <label>Command</label>
          <textarea v-model="actionConfig.command" class="textarea" placeholder="echo Hello"></textarea>
        </div>

        <div v-if="actionType === 'hotkey'" class="form-group">
          <label>Hotkey Combination</label>
          <div class="hotkey-selector-container">
            <div class="hotkey-input-wrapper">
              <input 
                v-model="hotkeyString" 
                type="text" 
                class="input hotkey-input" 
                placeholder="Click To Assign Via Keyboard Input"
                readonly
                @click="toggleHotkeyDropdown"
              />
              <button 
                class="dropdown-arrow" 
                @click="toggleHotkeyDropdown"
                :class="{ 'open': showHotkeyDropdown }"
              >
                <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
              </button>
            </div>
            
            <!-- Hotkey Dropdown -->
            <div v-if="showHotkeyDropdown" class="hotkey-dropdown">
              <div class="hotkey-dropdown-header">
                <h4>Manually Select Hotkeys</h4>
              </div>
              
              <div class="hotkey-categories">
                <!-- Letters and Numbers -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('letters')">
                    <span>Letters And Numbers</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('letters') }" />
                  </div>
                  <div v-if="expandedCategories.includes('letters')" class="category-content">
                    <div class="key-grid">
                      <button 
                        v-for="key in letterKeys" 
                        :key="key" 
                        class="key-button"
                        @click="addKeyToCombination(key)"
                      >
                        {{ key.toUpperCase() }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Navigation Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('navigation')">
                    <span>Navigation Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('navigation') }" />
                  </div>
                  <div v-if="expandedCategories.includes('navigation')" class="category-content">
                    <div class="key-list">
                      <button 
                        v-for="key in navigationKeys" 
                        :key="key.value" 
                        class="key-button"
                        @click="addKeyToCombination(key.value)"
                      >
                        <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                        {{ key.label }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Function Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('function')">
                    <span>Function Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('function') }" />
                  </div>
                  <div v-if="expandedCategories.includes('function')" class="category-content">
                    <div class="key-grid">
                      <button 
                        v-for="key in functionKeys" 
                        :key="key" 
                        class="key-button"
                        @click="addKeyToCombination(key)"
                      >
                        {{ key.toUpperCase() }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Modifier Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('modifiers')">
                    <span>Modifier Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('modifiers') }" />
                  </div>
                  <div v-if="expandedCategories.includes('modifiers')" class="category-content">
                    <div class="key-list">
                      <button 
                        v-for="key in modifierKeys" 
                        :key="key.value" 
                        class="key-button modifier-key"
                        @click="addKeyToCombination(key.value)"
                      >
                        <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                        {{ key.label }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Other Keys -->
                <div class="hotkey-category">
                  <div class="category-header" @click="toggleCategory('other')">
                    <span>Other Keys</span>
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" :class="{ 'rotated': expandedCategories.includes('other') }" />
                  </div>
                  <div v-if="expandedCategories.includes('other')" class="category-content">
                    <div class="key-list">
                      <button 
                        v-for="key in otherKeys" 
                        :key="key.value" 
                        class="key-button"
                        @click="addKeyToCombination(key.value)"
                      >
                        <FontAwesomeIcon v-if="key.icon" :icon="key.icon" />
                        {{ key.label }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Current Combination Display -->
              <div class="current-combination">
                <div class="combination-label">Current Combination:</div>
                <div class="combination-display">
                  <span 
                    v-for="(key, index) in currentKeyCombination" 
                    :key="index" 
                    class="key-chip"
                  >
                    {{ key }}
                    <button class="remove-key" @click="removeKeyFromCombination(index)">
                      <FontAwesomeIcon :icon="['fas', 'times']" />
                    </button>
                  </span>
                </div>
                <div class="combination-actions">
                  <button class="btn btn-secondary btn-sm" @click="clearCombination">Clear All</button>
                  <button class="btn btn-primary btn-sm" @click="applyCombination">Apply</button>
                </div>
              </div>
            </div>
          </div>
          <p class="form-help">Click the dropdown to manually select keys, or use keyboard input for quick assignment</p>
        </div>

        <!-- System Metric Configuration -->
        <div v-if="actionType === 'system_metric'" class="form-group">
          <label>Metric Type</label>
          <select v-model="actionConfig.metric_type" class="select">
            <option value="cpu">CPU Usage</option>
            <option value="memory">Memory (RAM)</option>
            <option value="disk">Disk Space</option>
            <option value="network">Network Traffic</option>
            <option value="temperature">Temperature</option>
            <option value="battery">Battery</option>
            <option value="processes">Processes</option>
          </select>
          <p class="form-help">Button will display live metrics with auto-refresh</p>
        </div>

        <div v-if="actionType === 'system_metric'" class="form-group">
          <label>Refresh Interval (seconds)</label>
          <input 
            v-model.number="actionConfig.refresh_interval" 
            type="number" 
            class="input" 
            min="1" 
            max="60"
            placeholder="5"
          />
          <p class="form-help">How often to update the metric (default: 5 seconds)</p>
        </div>

        <!-- Individual Metric Configuration -->
        <div v-if="isMetricType" class="form-group">
          <label>Refresh Interval (seconds)</label>
          <input 
            v-model.number="actionConfig.refresh_interval" 
            type="number" 
            class="input" 
            min="1" 
            max="60"
            placeholder="5"
          />
          <p class="form-help">How often to update the metric (default: 5 seconds)</p>
        </div>

        <!-- World Clock Configuration -->
        <div v-if="actionType === 'time_world_clock'" class="form-group">
          <label>Timezone</label>
          <select v-model="actionConfig.timezone" class="select">
            <option value="local">Local Time</option>
            <option value="America/New_York">New York (EST/EDT)</option>
            <option value="America/Chicago">Chicago (CST/CDT)</option>
            <option value="America/Denver">Denver (MST/MDT)</option>
            <option value="America/Los_Angeles">Los Angeles (PST/PDT)</option>
            <option value="Europe/London">London (GMT/BST)</option>
            <option value="Europe/Paris">Paris (CET/CEST)</option>
            <option value="Asia/Tokyo">Tokyo (JST)</option>
            <option value="Asia/Shanghai">Shanghai (CST)</option>
            <option value="Asia/Dubai">Dubai (GST)</option>
            <option value="Australia/Sydney">Sydney (AEST/AEDT)</option>
          </select>
        </div>

        <!-- Timer Configuration -->
        <div v-if="actionType === 'time_timer'" class="form-group">
          <label>Timer Duration (seconds)</label>
          <input 
            v-model.number="actionConfig.timer_duration" 
            type="number" 
            class="input" 
            min="0"
            placeholder="0"
          />
          <p class="form-help">Initial duration (0 for stopwatch mode)</p>
        </div>

        <!-- Countdown Configuration -->
        <div v-if="actionType === 'time_countdown'" class="form-group">
          <label>Countdown Target Date/Time</label>
          <input 
            v-model="actionConfig.countdown_target" 
            type="datetime-local" 
            class="input"
          />
          <p class="form-help">Leave empty to countdown until tomorrow</p>
        </div>

        <!-- Weather Configuration -->
        <div v-if="actionType === 'weather'" class="form-group">
          <label>Location</label>
          <input 
            v-model="actionConfig.weather_location" 
            type="text" 
            class="input" 
            placeholder="auto (or enter city name)"
          />
          <p class="form-help">Enter city name or "auto" for automatic location</p>
        </div>

        <div v-if="actionType === 'weather'" class="form-group">
          <label>Refresh Interval (minutes)</label>
          <input 
            v-model.number="actionConfig.refresh_interval" 
            type="number" 
            class="input" 
            min="5" 
            max="120"
            placeholder="15"
          />
          <p class="form-help">How often to update weather data (default: 15 minutes)</p>
        </div>

        <div v-if="actionType === 'system_control'" class="form-group">
          <label>System Action</label>
          <select v-model="actionConfig.action" class="select">
            <option value="volume_up">Volume Up</option>
            <option value="volume_down">Volume Down</option>
            <option value="volume_mute">Mute/Unmute</option>
            <option value="media_play_pause">Play/Pause</option>
            <option value="media_next">Next Track</option>
            <option value="media_previous">Previous Track</option>
            <option value="fullscreen">Full Screen</option>
          </select>
        </div>

        <div v-if="actionType === 'cross_platform'" class="form-group">
          <label>Cross-Platform Action</label>
          <select v-model="actionConfig.action" class="select">
            <optgroup label="System Control">
              <option value="shutdown">Shutdown</option>
              <option value="restart">Restart</option>
              <option value="sleep">Sleep</option>
              <option value="lock_screen">Lock Screen</option>
            </optgroup>
            <optgroup label="Volume Control">
              <option value="volume_up">Volume Up</option>
              <option value="volume_down">Volume Down</option>
              <option value="volume_mute">Mute</option>
              <option value="volume_unmute">Unmute</option>
            </optgroup>
            <optgroup label="Brightness Control">
              <option value="brightness_up">Brightness Up</option>
              <option value="brightness_down">Brightness Down</option>
              <option value="brightness_set">Set Brightness</option>
            </optgroup>
            <optgroup label="Media Control">
              <option value="media_play_pause">Play/Pause</option>
              <option value="media_next">Next Track</option>
              <option value="media_previous">Previous Track</option>
              <option value="media_stop">Stop</option>
            </optgroup>
            <optgroup label="Web & Apps">
              <option value="open_url">Open URL</option>
              <option value="open_app">Open Application</option>
              <option value="open_folder">Open Folder</option>
              <option value="open_file">Open File</option>
              <option value="screenshot">Screenshot</option>
            </optgroup>
          </select>
        </div>

        <!-- Cross-platform action specific configuration -->
        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_url'" class="form-group">
          <label>URL</label>
          <input v-model="actionConfig.url" type="text" class="input" placeholder="https://example.com" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_app'" class="form-group">
          <label>Application Path/Name</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="notepad.exe" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_folder'" class="form-group">
          <label>Folder Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="C:\" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_file'" class="form-group">
          <label>File Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="C:\Windows\System32\notepad.exe" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'screenshot'" class="form-group">
          <label>Screenshot Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="screenshot.png" />
        </div>

        <div v-if="actionType === 'cross_platform' && ['volume_up', 'volume_down', 'brightness_up', 'brightness_down'].includes(actionConfig.action)" class="form-group">
          <label>Step Size</label>
          <input v-model.number="actionConfig.step" type="number" class="input" min="1" max="100" placeholder="10" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'brightness_set'" class="form-group">
          <label>Brightness Level (0-100)</label>
          <input v-model.number="actionConfig.brightness" type="number" class="input" min="0" max="100" placeholder="50" />
        </div>

        <!-- Page Navigation Actions -->
        <div v-if="actionType === 'next_page' || actionType === 'previous_page'" class="form-group">
          <div class="info-message">
            <FontAwesomeIcon :icon="['fas', 'info-circle']" />
            <p>This button will navigate to the {{ actionType === 'next_page' ? 'next' : 'previous' }} page in the current scene.</p>
          </div>
        </div>

        <div class="form-group">
          <label>Tooltip (optional)</label>
          <input v-model="editedButton.tooltip" type="text" class="input" placeholder="Button description" />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="editedButton.enabled" type="checkbox" />
            <span>Enabled</span>
          </label>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="handleSave">Save</button>
      </div>
    </div>
  </div>

  <IconPicker 
    v-if="showIconPicker" 
    @select="handleIconSelect" 
    @close="showIconPicker = false" 
  />

    <!-- Asset Picker Modal -->
    <AssetPicker
      v-if="showAssetPicker"
      :type="showAssetPicker"
      :title="getAssetPickerTitle(showAssetPicker)"
      @close="showAssetPicker = null"
      @select="handleAssetSelect"
    />

    <!-- Actions Sidebar -->
    <ButtonActionsSidebar
      :is-open="showActionsSidebar"
      @close="showActionsSidebar = false"
      @select-action="handleActionSelection"
    />
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted, onMounted } from 'vue'
import type { Button, ButtonAction, ActionType } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useDashboardStore } from '@/stores/dashboard'
import IconPicker from './IconPicker.vue'
import MediaPicker from './MediaPicker.vue'
import AssetPicker from './AssetPicker.vue'
import ButtonActionsSidebar from './ButtonActionsSidebar.vue'
import type { AssetMetadata } from '@/utils/assetManager'

interface Props {
  button: Button
  profileId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  save: [button: Button]
  close: []
  saveProfile: []
}>()

const editedButton = ref<Button>(JSON.parse(JSON.stringify(props.button)))
const showIconPicker = ref(false)
const showAssetPicker = ref<'icon' | 'animation' | 'background' | null>(null)
const showActionsSidebar = ref(false)

const actionType = ref<ActionType | ''>(props.button.action?.type || '')
const actionConfig = ref<Record<string, any>>(props.button.action?.config || {})
const hotkeyString = ref(props.button.action?.config?.keys?.join(', ') || '')

// Hotkey dropdown state
const showHotkeyDropdown = ref(false)
const expandedCategories = ref<string[]>([])
const currentKeyCombination = ref<string[]>([])

// Key definitions
const letterKeys = ref([
  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
])

const navigationKeys = ref([
  { value: 'left', label: 'Left', icon: ['fas', 'arrow-left'] },
  { value: 'up', label: 'Up', icon: ['fas', 'arrow-up'] },
  { value: 'right', label: 'Right', icon: ['fas', 'arrow-right'] },
  { value: 'down', label: 'Down', icon: ['fas', 'arrow-down'] },
  { value: 'tab', label: 'Tab', icon: ['fas', 'arrow-right'] },
  { value: 'caps', label: 'Caps Lock', icon: ['fas', 'lock'] },
  { value: 'space', label: 'Space', icon: ['fas', 'minus'] },
  { value: 'escape', label: 'Escape', icon: ['fas', 'times'] },
  { value: 'enter', label: 'Enter', icon: ['fas', 'arrow-down'] },
  { value: 'backspace', label: 'Backspace', icon: ['fas', 'arrow-left'] },
  { value: 'home', label: 'Home', icon: ['fas', 'home'] },
  { value: 'end', label: 'End', icon: ['fas', 'stop'] },
  { value: 'pageup', label: 'Page Up', icon: ['fas', 'chevron-up'] },
  { value: 'pagedown', label: 'Page Down', icon: ['fas', 'chevron-down'] },
  { value: 'insert', label: 'Insert', icon: ['fas', 'plus'] },
  { value: 'delete', label: 'Delete', icon: ['fas', 'trash'] }
])

const functionKeys = ref([
  'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12'
])

const modifierKeys = ref([
  { value: 'ctrl', label: 'Ctrl', icon: ['fas', 'keyboard'] },
  { value: 'alt', label: 'Alt', icon: ['fas', 'keyboard'] },
  { value: 'shift', label: 'Shift', icon: ['fas', 'keyboard'] },
  { value: 'win', label: 'Windows', icon: ['fab', 'windows'] }
])

const otherKeys = ref([
  { value: 'print', label: 'Print Screen', icon: ['fas', 'print'] },
  { value: 'scroll', label: 'Scroll Lock', icon: ['fas', 'lock'] },
  { value: 'pause', label: 'Pause Break', icon: ['fas', 'pause'] },
  { value: 'numlock', label: 'Num Lock', icon: ['fas', 'lock'] },
  { value: 'menu', label: 'Menu', icon: ['fas', 'bars'] }
])

// Macro steps management
interface MacroStepUI {
  type: 'hotkey' | 'delay' | 'text' | 'click' | 'button'
  keysString?: string
  keys?: string[]
  delay?: number
  text?: string
  clickX?: number
  clickY?: number
  position?: { x: number; y: number }
  buttonId?: string
}

const macroSteps = ref<MacroStepUI[]>([])

// Visual macro builder state
const showMacroStepSelector = ref(false)
const editingStepIndex = ref<number | null>(null)
const editingStep = ref<MacroStepUI | null>(null)

// Macro hotkey dropdown state
const showMacroHotkeyDropdown = ref(false)
const expandedMacroCategories = ref<string[]>([])
const currentMacroKeyCombination = ref<string[]>([])

// Available buttons for macro selection
const availableButtons = computed(() => {
  const dashboardStore = useDashboardStore()
  const currentScene = dashboardStore.currentScene
  if (!currentScene) return []
  
  // Get all buttons from all pages in the current scene
  const allButtons: Button[] = []
  currentScene.pages.forEach(page => {
    page.buttons.forEach(button => {
      // Exclude the current button being edited to avoid recursion
      if (button.id !== props.button.id) {
        allButtons.push(button)
      }
    })
  })
  
  return allButtons
})

// Performance Monitor metrics
const performanceMetricOptions = [
  { value: 'memory', label: 'Memory' },
  { value: 'cpu_usage', label: 'CPU usage' },
  { value: 'cpu_temperature', label: 'CPU temperature' },
  { value: 'cpu_frequency', label: 'CPU frequency' },
  { value: 'cpu_package_power', label: 'CPU package power' },
  { value: 'internet_speed', label: 'Internet speed' },
  { value: 'harddisk', label: 'Harddisk' },
  { value: 'gpu_temperature', label: 'GPU temperature' },
  { value: 'gpu_core_frequency', label: 'GPU core frequency' },
  { value: 'gpu_core_usage', label: 'Gpu Core Usage' },
  { value: 'gpu_memory_frequency', label: 'GPU memory frequency' },
  { value: 'gpu_memory_usage', label: 'Gpu Memory Usage' },
]

const selectedPerformanceMetrics = ref<string[]>([])

// Check if action type is a metric type
const isMetricType = computed(() => {
  return actionType.value?.startsWith('metric_')
})

// Initialize macro steps from existing button action
if (props.button.action?.type === 'macro' && props.button.action.macro_steps) {
  macroSteps.value = props.button.action.macro_steps.map((step: any) => ({
    type: step.type,
    keysString: step.keys?.join(', ') || '',
    keys: step.keys || [],
    delay: step.delay,
    text: step.text,
    clickX: step.position?.x,
    clickY: step.position?.y,
    position: step.position
  }))
}

// Color palette for background color selection
const colorPalette = ref([
  '#2c3e50', '#34495e', '#7f8c8d', '#95a5a6', '#bdc3c7', '#ecf0f1',
  '#e74c3c', '#c0392b', '#e67e22', '#d35400', '#f39c12', '#f1c40f',
  '#27ae60', '#16a085', '#2ecc71', '#1abc9c', '#3498db', '#2980b9',
  '#9b59b6', '#8e44ad', '#e91e63', '#ad1457', '#673ab7', '#512da8',
  '#795548', '#5d4037', '#607d8b', '#455a64', '#000000', '#ffffff'
])

// Media picker value
const mediaValue = ref<{ url: string; type: string } | null>(
  props.button.media_url && props.button.media_type 
    ? { url: props.button.media_url, type: props.button.media_type }
    : null
)

watch(actionType, (newType) => {
  if (!newType) {
    editedButton.value.action = undefined
  } else {
    editedButton.value.action = {
      type: newType,
      config: actionConfig.value
    }
  }
})

watch(actionConfig, (newConfig) => {
  if (editedButton.value.action) {
    editedButton.value.action.config = newConfig
  }
}, { deep: true })

// Watch for media type changes to clear media when type is removed
watch(() => editedButton.value.media_type, (newType) => {
  if (!newType) {
    editedButton.value.media_url = undefined
    mediaValue.value = null
  }
})

function handleActionTypeChange() {
  actionConfig.value = {}
  hotkeyString.value = ''
}

function updateHotkeyConfig() {
  actionConfig.value.keys = hotkeyString.value
    .split(',')
    .map(k => k.trim())
    .filter(k => k.length > 0)
}

// Hotkey dropdown functions
function toggleHotkeyDropdown() {
  showHotkeyDropdown.value = !showHotkeyDropdown.value
  
  if (showHotkeyDropdown.value) {
    // Initialize current combination from existing hotkey string
    if (hotkeyString.value) {
      currentKeyCombination.value = hotkeyString.value
        .split(',')
        .map(k => k.trim())
        .filter(k => k.length > 0)
    } else {
      currentKeyCombination.value = []
    }
  }
}

function toggleCategory(category: string) {
  const index = expandedCategories.value.indexOf(category)
  if (index > -1) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(category)
  }
}

function addKeyToCombination(key: string) {
  // Don't add duplicate keys
  if (!currentKeyCombination.value.includes(key)) {
    currentKeyCombination.value.push(key)
  }
}

function removeKeyFromCombination(index: number) {
  currentKeyCombination.value.splice(index, 1)
}

function clearCombination() {
  currentKeyCombination.value = []
}

function applyCombination() {
  if (currentKeyCombination.value.length > 0) {
    hotkeyString.value = currentKeyCombination.value.join(', ')
    updateHotkeyConfig()
  }
  showHotkeyDropdown.value = false
}

function handleIconSelect(icon: string) {
  editedButton.value.icon = icon
  editedButton.value.icon_type = 'fontawesome'
  showIconPicker.value = false
}

function getAssetPickerTitle(type: string): string {
  switch (type) {
    case 'icon': return 'Select Icon'
    case 'animation': return 'Select Animation'
    case 'background': return 'Select Background'
    default: return 'Select Asset'
  }
}

function handleAssetSelect(asset: AssetMetadata) {
  switch (showAssetPicker.value) {
    case 'icon':
      if (asset.format === 'fontawesome') {
        editedButton.value.icon_type = 'fontawesome'
        editedButton.value.icon = asset.icon
      } else {
        editedButton.value.icon_type = 'custom'
        editedButton.value.icon = asset.url
      }
      break
    
    case 'animation':
      editedButton.value.media_url = asset.url
      editedButton.value.media_type = asset.format === 'gif' ? 'gif' : 'video'
      break
    
    case 'background':
      if (asset.format === 'css') {
        editedButton.value.style = editedButton.value.style || {}
        editedButton.value.style.effect = 'gradient'
        editedButton.value.style.gradient = asset.css
      } else {
        // Handle image backgrounds
        editedButton.value.media_url = asset.url
        editedButton.value.media_type = 'image'
      }
      break
  }
  
  showAssetPicker.value = null
}

function handleMediaChange(value: { url: string; type: string } | null) {
  if (value) {
    editedButton.value.media_url = value.url
    editedButton.value.media_type = value.type
  } else {
    editedButton.value.media_url = undefined
    editedButton.value.media_type = undefined
  }
}

function getMediaPlaceholder(mediaType: string) {
  switch (mediaType) {
    case 'image':
      return 'https://example.com/image.png'
    case 'gif':
      return 'https://example.com/animation.gif'
    case 'video':
      return 'https://example.com/video.mp4'
    default:
      return ''
  }
}

function getMediaHelpText(mediaType: string) {
  switch (mediaType) {
    case 'image':
      return 'Static image will be displayed as background behind the icon'
    case 'gif':
      return 'GIF animation will loop continuously behind the icon'
    case 'video':
      return 'Video will autoplay, loop, and be muted behind the icon'
    default:
      return ''
  }
}

function selectColor(color: string) {
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  editedButton.value.style.backgroundColor = color
}

function updateBackgroundColor(event: Event) {
  const target = event.target as HTMLInputElement
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  editedButton.value.style.backgroundColor = target.value
}

function updateIconSize(event: Event) {
  const target = event.target as HTMLInputElement
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  editedButton.value.style.iconSize = parseInt(target.value)
}

// Macro step functions
// Visual macro builder functions
function addMacroStep(type: 'hotkey' | 'delay' | 'text' | 'click') {
  const newStep: MacroStepUI = {
    type,
    keysString: '',
    keys: [],
    delay: 500,
    text: '',
    clickX: 0,
    clickY: 0
  }
  
  macroSteps.value.push(newStep)
  showMacroStepSelector.value = false
  
  // Auto-edit the new step
  editMacroStep(macroSteps.value.length - 1)
}

function removeMacroStep(index: number) {
  macroSteps.value.splice(index, 1)
}

function editMacroStep(index: number) {
  editingStepIndex.value = index
  editingStep.value = { ...macroSteps.value[index] }
  
  // Initialize macro key combination if it's a hotkey step
  if (macroSteps.value[index].type === 'hotkey' && macroSteps.value[index].keysString) {
    currentMacroKeyCombination.value = macroSteps.value[index].keysString
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0)
  } else {
    currentMacroKeyCombination.value = []
  }
}

function closeStepEditor() {
  editingStepIndex.value = null
  editingStep.value = null
  showMacroHotkeyDropdown.value = false
}

function saveStepEditor() {
  if (editingStepIndex.value !== null && editingStep.value) {
    macroSteps.value[editingStepIndex.value] = { ...editingStep.value }
    closeStepEditor()
  }
}

function getStepIcon(type: string) {
  const icons: Record<string, any> = {
    'hotkey': ['fas', 'keyboard'],
    'delay': ['fas', 'clock'],
    'text': ['fas', 'keyboard'],
    'click': ['fas', 'mouse-pointer'],
    'button': ['fas', 'square']
  }
  return icons[type] || ['fas', 'question']
}

function getStepDescription(step: MacroStepUI): string {
  switch (step.type) {
    case 'hotkey':
      return step.keysString || 'Hotkey'
    case 'delay':
      return `${step.delay || 500}ms delay`
    case 'text':
      return step.text || 'Type text'
    case 'click':
      return step.clickX !== undefined && step.clickY !== undefined 
        ? `Click (${step.clickX}, ${step.clickY})`
        : 'Mouse click'
    case 'button':
      const button = availableButtons.value.find(b => b.id === step.buttonId)
      return button ? button.label : 'Button action'
    default:
      return 'Unknown step'
  }
}

function selectButtonForMacro(button: Button) {
  if (editingStep.value) {
    editingStep.value.buttonId = button.id
  }
}

function getButtonActionDescription(button: Button): string {
  if (!button.action) return 'No action'
  
  switch (button.action.type) {
    case 'hotkey':
      return 'Hotkey'
    case 'program':
      return 'Launch Program'
    case 'url':
      return 'Open URL'
    case 'command':
      return 'Run Command'
    case 'macro':
      return 'Macro'
    case 'system_metric':
      return 'System Metric'
    default:
      return button.action.type
  }
}

function getActionTypeDisplayName(actionType: string): string {
  const actionNames: Record<string, string> = {
    'url': 'Open URL',
    'program': 'Launch Program',
    'command': 'Run Command',
    'hotkey': 'Send Hotkey',
    'macro': 'Macro (Multiple Actions)',
    'multi_action': 'Multi-Action',
    'system_metric': 'System Metric Display',
    'metric_memory': 'Memory Monitor',
    'metric_cpu_usage': 'CPU Usage Monitor',
    'metric_cpu_temperature': 'CPU Temperature Monitor',
    'metric_cpu_frequency': 'CPU Frequency Monitor',
    'metric_cpu_power': 'CPU Power Monitor',
    'metric_internet_speed': 'Internet Speed Monitor',
    'metric_harddisk': 'Hard Disk Monitor',
    'metric_gpu_temperature': 'GPU Temperature Monitor',
    'metric_gpu_frequency': 'GPU Frequency Monitor',
    'metric_gpu_usage': 'GPU Usage Monitor',
    'metric_gpu_memory_freq': 'GPU Memory Frequency Monitor',
    'metric_gpu_memory_usage': 'GPU Memory Usage Monitor',
    'calendar': 'Calendar',
    'time_world_clock': 'World Time',
    'time_timer': 'Timer',
    'time_countdown': 'Countdown',
    'weather': 'Weather Query',
    'system_control': 'System Control',
    'cross_platform': 'Cross-Platform Action'
  }
  
  return actionNames[actionType] || actionType || 'No Action'
}

// Macro hotkey dropdown functions
function toggleMacroHotkeyDropdown() {
  showMacroHotkeyDropdown.value = !showMacroHotkeyDropdown.value
}

function toggleMacroCategory(category: string) {
  const index = expandedMacroCategories.value.indexOf(category)
  if (index > -1) {
    expandedMacroCategories.value.splice(index, 1)
  } else {
    expandedMacroCategories.value.push(category)
  }
}

function addKeyToMacroCombination(key: string) {
  if (!currentMacroKeyCombination.value.includes(key)) {
    currentMacroKeyCombination.value.push(key)
  }
}

function removeKeyFromMacroCombination(index: number) {
  currentMacroKeyCombination.value.splice(index, 1)
}

function clearMacroCombination() {
  currentMacroKeyCombination.value = []
}

function applyMacroCombination() {
  if (currentMacroKeyCombination.value.length > 0 && editingStep.value) {
    editingStep.value.keysString = currentMacroKeyCombination.value.join(', ')
    editingStep.value.keys = [...currentMacroKeyCombination.value]
  }
  showMacroHotkeyDropdown.value = false
}

function handleActionSelection(selectedActionType: string) {
  actionType.value = selectedActionType as ActionType
  actionConfig.value = {}
  hotkeyString.value = ''
  showActionsSidebar.value = false
  
  // Set default labels based on action type
  const actionLabels: Record<string, string> = {
    'metric_memory': 'Memory',
    'metric_cpu_usage': 'CPU',
    'metric_cpu_temperature': 'CPU Temp',
    'metric_cpu_frequency': 'CPU Freq',
    'metric_cpu_power': 'CPU Power',
    'metric_internet_speed': 'Internet',
    'metric_harddisk': 'Disk',
    'metric_gpu_temperature': 'GPU Temp',
    'metric_gpu_frequency': 'GPU Freq',
    'metric_gpu_usage': 'GPU Usage',
    'metric_gpu_memory_freq': 'GPU Mem Freq',
    'metric_gpu_memory_usage': 'GPU Mem',
    'calendar': 'Calendar',
    'time_world_clock': 'World Clock',
    'time_timer': 'Timer',
    'time_countdown': 'Countdown',
    'weather': 'Weather',
    'next_page': 'Next Page',
    'previous_page': 'Previous Page'
  }
  
  if (actionLabels[selectedActionType]) {
    editedButton.value.label = actionLabels[selectedActionType]
  }
}

function handleSaveProfile() {
  emit('saveProfile')
}

function handleSave() {
  // Ensure style object exists
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  
  // Set default values if not provided
  if (!editedButton.value.style.backgroundColor) {
    editedButton.value.style.backgroundColor = '#2c3e50'
  }
  if (!editedButton.value.style.iconSize) {
    editedButton.value.style.iconSize = 32
  }
  
  // Update action if configured
  if (actionType.value) {
    if (!editedButton.value.action) {
      editedButton.value.action = {
        type: actionType.value,
        config: {}
      }
    }
    
    editedButton.value.action.type = actionType.value
    editedButton.value.action.config = actionConfig.value
    
    // Handle macro steps
    if (actionType.value === 'macro') {
      editedButton.value.action.macro_steps = macroSteps.value.map(step => {
        const macroStep: any = {
          type: step.type
        }
        
        if (step.type === 'hotkey' && step.keys) {
          macroStep.keys = step.keys
        } else if (step.type === 'delay') {
          macroStep.delay = step.delay || 500
        } else if (step.type === 'text') {
          macroStep.text = step.text || ''
        } else if (step.type === 'click') {
          if (step.clickX !== undefined && step.clickY !== undefined) {
            macroStep.position = { x: step.clickX, y: step.clickY }
          }
        }
        
        return macroStep
      })
    }
    
    // Handle performance monitor metrics
    if (actionType.value === 'performance_monitor') {
      editedButton.value.action.performance_metrics = selectedPerformanceMetrics.value
    }
    
    // Handle time options
    if (actionType.value === 'time_options') {
      editedButton.value.action.time_option = actionConfig.value.time_option
      editedButton.value.action.timezone = actionConfig.value.timezone
      editedButton.value.action.timer_duration = actionConfig.value.timer_duration
      editedButton.value.action.countdown_target = actionConfig.value.countdown_target
    }
    
    // Handle weather query
    if (actionType.value === 'weather_query') {
      editedButton.value.action.weather_location = actionConfig.value.weather_location || 'auto'
    }
  }
  
  emit('save', editedButton.value)
}

// Click outside to close dropdown
function handleClickOutside(event: Event) {
  const target = event.target as HTMLElement
  const dropdown = document.querySelector('.hotkey-selector-container')
  
  if (dropdown && !dropdown.contains(target)) {
    showHotkeyDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  showHotkeyDropdown.value = false
})
</script>

<style scoped>
.button-editor {
  width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.save-profile-btn {
  background: var(--color-success);
  border: none;
  font-size: 1.25rem;
  color: white;
  cursor: pointer;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.save-profile-btn:hover {
  background: var(--color-success-dark);
  transform: scale(1.05);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text);
}

.modal-body {
  margin-bottom: var(--spacing-lg);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--color-text);
}

.small-label {
  font-size: 0.75rem;
  font-weight: normal;
  color: var(--color-text-secondary);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.form-help {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  margin-bottom: 0;
}

/* Color Picker Styles */
.color-picker-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.current-color {
  width: 60px;
  height: 40px;
  border-radius: var(--radius-md);
  border: 2px solid var(--color-border);
  position: relative;
  cursor: pointer;
  overflow: hidden;
}

.color-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0;
}

.color-palette {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--spacing-xs);
  max-width: 300px;
}

.color-swatch {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.color-swatch:hover {
  transform: scale(1.1);
  border-color: var(--color-primary);
}

.color-swatch.active {
  border-color: var(--color-primary);
  border-width: 3px;
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

/* Icon Size Controls */
.icon-size-controls {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.icon-size-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--color-border);
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
}

.icon-size-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface-solid);
  box-shadow: var(--shadow-sm);
}

.icon-size-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface-solid);
  box-shadow: var(--shadow-sm);
}

.icon-size-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.icon-size-display span {
  font-weight: 500;
  color: var(--color-text);
  font-size: 0.875rem;
}

.icon-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background-color: var(--color-surface-solid);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

/* Macro Editor Styles */
.macro-editor {
  margin: var(--spacing-md) 0;
}

.macro-step {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.macro-step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.step-number {
  font-weight: 600;
  color: var(--color-primary);
  font-size: 0.875rem;
}

.step-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.btn-icon {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  cursor: pointer;
  color: var(--color-text);
  transition: all var(--transition-fast);
  font-size: 0.75rem;
}

.btn-icon:hover:not(:disabled) {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon.btn-danger:hover:not(:disabled) {
  background: #ef4444;
  border-color: #ef4444;
}

.macro-step-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.small-label {
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: var(--spacing-xs);
  display: block;
}

.form-help-sm {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  max-height: 300px;
  overflow-y: auto;
}

.checkbox-group .checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  transition: background-color 0.2s;
}

.checkbox-group .checkbox-label:hover {
  background-color: var(--color-background);
}

.checkbox-group input[type="checkbox"] {
  cursor: pointer;
}

.btn-sm {
  font-size: 0.875rem;
  padding: var(--spacing-xs) var(--spacing-sm);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
}

.info-message {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: rgba(52, 152, 219, 0.1);
  border: 1px solid rgba(52, 152, 219, 0.3);
  border-radius: var(--radius-md);
  color: var(--color-text);
}

.info-message svg {
  color: var(--color-primary);
  flex-shrink: 0;
}

.info-message p {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Hotkey Dropdown Styles */
.hotkey-selector-container {
  position: relative;
}

.hotkey-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.hotkey-input {
  flex: 1;
  cursor: pointer;
  background-color: var(--color-surface);
  border: 2px solid var(--color-border);
  transition: all 0.2s ease;
  padding-right: 40px;
}

.hotkey-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.dropdown-arrow {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  transition: transform 0.2s ease;
}

.dropdown-arrow.open {
  transform: rotate(180deg);
}

.hotkey-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  max-height: 400px;
  overflow-y: auto;
  margin-top: 4px;
}

.hotkey-dropdown-header {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.hotkey-dropdown-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.hotkey-categories {
  padding: var(--spacing-sm);
}

.hotkey-category {
  margin-bottom: var(--spacing-sm);
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.category-header:hover {
  background: var(--color-hover);
}

.category-header svg {
  transition: transform 0.2s ease;
}

.category-header svg.rotated {
  transform: rotate(90deg);
}

.category-content {
  margin-top: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.key-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
  gap: var(--spacing-xs);
}

.key-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.key-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  min-height: 32px;
}

.key-button:hover {
  background: var(--color-hover);
  border-color: var(--color-primary);
}

.key-button.modifier-key {
  background: rgba(52, 152, 219, 0.1);
  border-color: var(--color-primary);
}

.key-button.modifier-key:hover {
  background: rgba(52, 152, 219, 0.2);
}

.current-combination {
  padding: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

.combination-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.combination-display {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
  min-height: 32px;
  align-items: center;
}

.key-chip {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-primary);
  color: white;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
}

.remove-key {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.remove-key:hover {
  background: rgba(255, 255, 255, 0.2);
}

.combination-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

.form-help {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  line-height: 1.4;
}

/* Visual Macro Builder Styles */
.macro-builder-container {
  position: relative;
}

.macro-builder {
  margin-bottom: var(--spacing-md);
}

.macro-steps-display {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
  min-height: 60px;
  padding: var(--spacing-md);
  background: var(--color-surface);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
}

.macro-step-chip {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--color-primary);
  color: white;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  font-weight: 500;
}

.macro-step-chip:hover {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
}

.step-number {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.step-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.remove-step {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.remove-step:hover {
  background: rgba(255, 255, 255, 0.2);
}

.add-step-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-secondary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  font-weight: 500;
}

.add-step-btn:hover {
  background: var(--color-secondary-dark);
  transform: translateY(-1px);
}

.macro-step-selector {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  margin-top: 4px;
}

.selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.selector-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-selector {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-selector:hover {
  background: var(--color-hover);
}

.step-types {
  padding: var(--spacing-md);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-sm);
}

.step-type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.step-type-btn:hover {
  border-color: var(--color-primary);
  background: var(--color-hover);
  transform: translateY(-2px);
}

.step-type-btn svg {
  font-size: 1.5rem;
  color: var(--color-primary);
}

.step-type-btn span {
  font-weight: 600;
  color: var(--color-text);
}

.step-type-btn small {
  color: var(--color-text-secondary);
  font-size: 0.75rem;
}

.macro-step-editor {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  margin-top: 4px;
  max-height: 500px;
  overflow-y: auto;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.editor-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-editor {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-editor:hover {
  background: var(--color-hover);
}

.step-editor-content {
  padding: var(--spacing-md);
}

.editor-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

/* Button Selector Styles */
.button-selector-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.button-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
}

.button-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.button-option:hover {
  border-color: var(--color-primary);
  background: var(--color-hover);
}

.button-option.selected {
  border-color: var(--color-primary);
  background: rgba(52, 152, 219, 0.1);
}

.button-preview {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: white;
  border-radius: var(--radius-sm);
  font-size: 1rem;
}

.custom-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.button-info {
  flex: 1;
  min-width: 0;
}

.button-label {
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.button-action {
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Action Type Display Styles */
.action-type-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.action-type-text {
  font-weight: 600;
  color: var(--color-text);
  flex: 1;
}

.action-type-badge {
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.action-type-badge.no-action {
  background: var(--color-background);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.action-type-badge:not(.no-action) {
  background: var(--color-primary);
  color: white;
}
</style>

