project "date"

dofile(_BUILD_DIR .. "/static_library.lua")

configuration { "*" }

uuid "422C8CCD-5D01-4D78-B0D9-2041681C4EE8"

includedirs {
  "include",
}

files {
  "src/**.cpp",
}

if (_PLATFORM_ANDROID) then
end

if (_PLATFORM_COCOA) then
end

if (_PLATFORM_IOS) then
end

if (_PLATFORM_LINUX) then
end

if (_PLATFORM_MACOS) then
end

if (_PLATFORM_WINDOWS) then
end

if (_PLATFORM_WINUWP) then
end
