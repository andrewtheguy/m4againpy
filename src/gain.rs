use std::path::Path;

use crate::aac;
use crate::error::Result;

/// Apply a static `gain_steps` (1 step ≈ 1.5 dB) to AAC/M4A bytes.
///
/// Returns a new `Vec<u8>` with `global_gain` fields rewritten. `gain_steps == 0`
/// returns a clone of the input. Saturating at 0..=255; silence (gain==0) is
/// skipped.
pub fn aac_apply_gain(data: &[u8], gain_steps: i32) -> Result<Vec<u8>> {
    let mut out = data.to_vec();
    if gain_steps == 0 {
        return Ok(out);
    }
    aac::apply_gain_to_bytes(&mut out, gain_steps)?;
    Ok(out)
}

/// Apply a static `gain_steps` to an AAC/M4A file in place. Returns the number
/// of `global_gain` locations actually modified. `gain_steps == 0` is a no-op
/// and does not rewrite the file.
pub fn aac_apply_gain_file(path: &Path, gain_steps: i32) -> Result<usize> {
    if gain_steps == 0 {
        return Ok(0);
    }
    let mut data = std::fs::read(path)?;
    let modified = aac::apply_gain_to_bytes(&mut data, gain_steps)?;
    if modified > 0 {
        std::fs::write(path, &data)?;
    }
    Ok(modified)
}
