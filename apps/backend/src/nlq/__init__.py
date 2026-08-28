"""Natural-language spatial query layer.

Distinct from `src.ai`, which is computer-vision inference over rasters. This
package turns a plain-language question into a *validated* structure and hands
it to the existing spatial engine; it never builds or executes SQL itself.
"""
