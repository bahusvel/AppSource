require 'xcodeproj'
xcproj = Xcodeproj::Project.open(ARGV[0])
xcproj.recreate_user_schemes
xcproj.save