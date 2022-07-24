from django.db.models import Lookup

class shasLookup(Lookup):
    lookup_name = 'shas'

    def as_sql(self, compiler, connection):

        lhs, lhs_params = self.process_lhs(compiler, connection)

        rhs, rhs_params = self.process_rhs(compiler, connection)

        params = lhs_params + rhs_params
        lst=rhs_params[0].replace("'","").replace('"','').split("=")
        lst[0]=lst[0].strip()
        lst[1]=lst[1].strip()
        if lst[1].lower() in ("none","null"):
            lst[1]="IS  NULL"
            return "JSON_EXTRACT(`%s`,'%s') %s" % (lhs, lst[0], lst[1]), []
        if lst[1].lower() in ("is not null", "is not none", "!null", "!none"):
            lst[1] = "IS NOT NULL"
            return "JSON_EXTRACT(`%s`,'%s') %s" % (lhs, lst[0],lst[1]),[]
        return "JSON_EXTRACT(%s,'%s')= %s" %(lhs, lst[0],rhs),[lst[1]]