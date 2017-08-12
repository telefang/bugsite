.PHONY: all compare_alpha compare_beta clean alpha beta

.SUFFIXES:
.SUFFIXES: .asm .o .gbc .png .wav .wikitext
.SECONDEXPANSION:

BASE_DIR := baseroms
BUILD_DIR := build

ROMS_ALPHA := ${BUILD_DIR}/bugsite_alpha.gbc
BASEROM_ALPHA := ${BASE_DIR}/baserom_alpha.gbc
ROMS_BETA := ${BUILD_DIR}/bugsite_beta.gbc
BASEROM_BETA := ${BASE_DIR}/baserom_beta.gbc

OBJS := component/bugvm/decode.o component/bugvm/optable.o component/bugvm/vm_state.o
OBJS_DIR := component/bugfs/directory.bugfs.o
OBJS_ALPHA := 
OBJS_BETA := 
OBJS_ALL := ${OBJS} ${OBJS_ALPHA} ${OBJS_BETA}

#Only Python 3 is supported this time.
PYTHON := python
PRET := pokemon-reverse-engineering-tools/pokemontools

$(foreach obj, $(OBJS), \
	$(eval $(obj:.o=)_dep := $(addprefix ${BUILD_DIR}/,$(shell $(PYTHON) utilities/scan_includes.py $(obj:.o=.asm)))) \
)

$(foreach obj, $(OBJS_ALPHA), \
	$(eval $(obj:.o=)_dep := $(addprefix ${BUILD_DIR}/,$(shell $(PYTHON) utilities/scan_includes.py $(obj:.o=.asm)))) \
)

$(foreach obj, $(OBJS_BETA), \
	$(eval $(obj:.o=)_dep := $(addprefix ${BUILD_DIR}/,$(shell $(PYTHON) utilities/scan_includes.py $(obj:.o=.asm)))) \
)

$(foreach obj, $(OBJS_DIR), \
	$(eval $(obj:.bugfs.o=)_dep := $(addprefix ${BUILD_DIR}/,$(shell $(PYTHON) utilities/bfsdeps.py $(obj:.bugfs.o=.bfs)))) \
)

# Link objects together to build a rom.
all: alpha beta

alpha: $(ROMS_ALPHA) compare_alpha

beta: $(ROMS_BETA) compare_beta

# Assemble source files into objects.
# Use rgbasm -h to use halts without nops.
$(OBJS_ALL:%.o=${BUILD_DIR}/%.o): $(BUILD_DIR)/%.o : %.asm $$($$*_dep)
	mkdir -p $(dir $@)
	rgbasm -h -o $@ $<

# Assemble the BugFS directory...
$(OBJS_DIR:%.bugfs.o=${BUILD_DIR}/%.bugfs.o): $(BUILD_DIR)/%.bugfs.o : %.bfs $$($$*_dep)
	mkdir -p $(dir $@)
	$(PYTHON) utilities/bfsbuild.py $@ $<

$(ROMS_ALPHA): $(OBJS:%.o=${BUILD_DIR}/%.o) $(OBJS_DIR:%.o=${BUILD_DIR}/%.o) $(OBJS_ALPHA:%.o=${BUILD_DIR}/%.o)
	rgblink -n $(ROMS_ALPHA:.gbc=.sym) -m $(ROMS_ALPHA:.gbc=.map) -O $(BASEROM_ALPHA) -o $@ $^
	rgbfix -v -C -i BAUJ -k 2N -l 0x33 -m 0x1B -p 0 -r 3 -t "BUGSITE ALP" $@

$(ROMS_BETA): $(OBJS:%.o=${BUILD_DIR}/%.o) $(OBJS_DIR:%.o=${BUILD_DIR}/%.o) $(OBJS_BETA:%.o=${BUILD_DIR}/%.o)
	rgblink -n $(ROMS_BETA:.gbc=.sym) -m $(ROMS_BETA:.gbc=.map) -O $(BASEROM_BETA) -o $@ $^
	rgbfix -v -C -i BBUJ -k 2N -l 0x33 -m 0x1B -p 0 -r 3 -t "BUGSITE BET" $@

# The compare target is a shortcut to check that the build matches the original roms exactly.
# This is for contributors to make sure a change didn't affect the contents of the rom.
# More thorough comparison can be made by diffing the output of hexdump -C against both roms.
compare_alpha: $(ROMS_ALPHA) $(BASEROM_ALPHA)
	cmp $^

compare_beta: $(ROMS_BETA) $(BASEROM_BETA)
	cmp $^

# Remove files generated by the build process.
clean:
	rm -f $(ROMS_ALPHA) $(OBJS) $(OBJS_ALPHA) $(ROMS_ALPHA:.gbc=.sym) $(ROMS_ALPHA:.gbc=.map) $(ROMS_BETA) $(OBJS_BETA) $(ROMS_BETA:.gbc=.sym) $(ROMS_BETA:.gbc=.map)
	find . \( -iname '*.1bpp' -o -iname '*.2bpp' -o -iname '*.pcm' -o -iname '*.scripttbl' \) -exec rm {} +

#This rule is needed if we want make to not die. It expects to see .inc files in
#the build directory now that we moved all resources there. We DO want to see
#.inc files as dependencies but I can't be arsed to fiddle with any more arcane
#makefile bullshit to get it to not prefix .inc files.
$(BUILD_DIR)/%.inc: %.inc
	cp $< $@

$(BUILD_DIR)/%.2bpp: %.png
	@rm -f $@
	@$(PYTHON) $(PRET)/gfx.py 2bpp $<

$(BUILD_DIR)/%.1bpp: %.png
	@rm -f $@
	@$(PYTHON) $(PRET)/gfx.py 1bpp $<
   
$(BUILD_DIR)/%.bugvm.bin: %.bvm
	mkdir -p $(dir $@)
	@$(PYTHON) utilities/bvmasm.py $< script/bugvm_strings.txt script/charmap.txt $@