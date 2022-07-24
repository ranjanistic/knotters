from django.db.models import Lookup

class hasLookup(Lookup):
    lookup_name = 'has'

    def as_sql(self, compiler, connection):

        lhs, lhs_params = self.process_lhs(compiler, connection)

        rhs, rhs_params = self.process_rhs(compiler, connection)
        sql, params = compiler.compile(self.lhs)
        params = lhs_params + rhs_params
        lst=rhs_params[0].replace("'","").replace('"','').split("=")
        lst[0]=lst[0].strip()
        lst[1]=lst[1].strip()
        if lst[1].isdigit():
            lst[1]=int(lst[1])
        if type(lst[1]) == type("a"):
            if lst[1].lower() in ("none","null"):
                lst[1]="IS NULL"
#                return "JSON_EXTRACT(`%s`,'%s') %s" % (lhs, lst[0], lst[1]), []
            elif lst[1].lower() in ("is not null", "is not none", "!null", "!none"):
                lst[1] = "IS NOT NULL"
            else:
                lst[1] = " = '%s'"%(lst[1])
        else:
            lst[1]=" = %s"%(lst[1])
  #      return "JSON_EXTRACT(`%s`,'%s') %s" % (lhs, lst[0],lst[1]),[]
        return "JSON_EXTRACT(%s,'%s')%s" %(lhs, lst[0],lst[1]),[]

